import os
from io import BytesIO

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from api.services.ai_agent import AIAgent
from api.services.contract_service import ContractService

contract_bp = Blueprint("contracts", __name__)
cs = ContractService()
agent = AIAgent()  # will use environment-configured GroqClient inside


# helper: extract text from uploaded file
def extract_text_from_file(file_storage):
    """
    Try DOCX then PDF then try decode fallback.
    Returns a string of extracted text.
    """
    filename = secure_filename(file_storage.filename or "file")
    content = file_storage.read()
    # try docx
    try:
        from docx import Document

        if filename.lower().endswith(".docx"):
            doc = Document(BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs if p.text]
            return "\n".join(paragraphs)
    except Exception:
        pass

    # try pypdf (formerly PyPDF2)
    try:
        import pypdf

        if filename.lower().endswith(".pdf"):
            reader = pypdf.PdfReader(BytesIO(content))
            pages = []
            for p in reader.pages:
                try:
                    pages.append(p.extract_text() or "")
                except Exception:
                    continue
            return "\n".join(pages)
    except Exception:
        pass

    # naive utf-8 decode fallback (may fail for binaries)
    try:
        return content.decode("utf-8")
    except Exception:
        # last-resort placeholder: ask client to provide text
        return ""


@contract_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_contract():
    user_id = get_jwt_identity()
    if "file" not in request.files:
        return jsonify({"success": False, "error": "File is required"}), 400
    file = request.files["file"]
    title = request.form.get("title") or file.filename or "Untitled Contract"
    extracted_text = extract_text_from_file(file)
    if not extracted_text:
        return jsonify(
            {
                "success": False,
                "error": "Could not extract text from file. Please provide a text/plain upload or a docx/pdf file.",
            }
        ), 400

    # call AI summarizer
    try:
        parsed, raw_xml = agent.summarize_contract(extracted_text, title=title)
    except RuntimeError as e:
        return jsonify(
            {"success": False, "error": "AI service unavailable", "details": str(e)}
        ), 503
    except ValueError as e:
        return jsonify(
            {
                "success": False,
                "error": "Unable to parse AI response",
                "details": str(e),
            }
        ), 422

    # Save summary only
    doc = cs.create_contract(
        user_id=user_id, title=title, summary=parsed, status="summarized"
    )
    return jsonify({"success": True, "data": doc}), 201


@contract_bp.route("", methods=["GET"])
@jwt_required()
def list_contracts():
    user_id = get_jwt_identity()
    items = cs.list_by_user(user_id)
    return jsonify({"success": True, "data": items}), 200


@contract_bp.route("/<string:contract_id>", methods=["GET"])
@jwt_required()
def get_contract(contract_id):
    user_id = get_jwt_identity()
    c = cs.get_by_id_and_user(contract_id, user_id)
    if not c:
        return jsonify({"success": False, "error": "Not found"}), 404
    out = {
        "id": str(c["_id"]),
        "title": c.get("title"),
        "status": c.get("status"),
        "uploadDate": c.get("uploadDate"),
        "summary": c.get("summary"),
    }
    return jsonify({"success": True, "data": out}), 200


@contract_bp.route("/<string:contract_id>", methods=["PUT"])
@jwt_required()
def update_contract(contract_id):
    user_id = get_jwt_identity()
    c = cs.get_by_id_and_user(contract_id, user_id)
    if not c:
        return jsonify({"success": False, "error": "Not found"}), 404
    updates = request.get_json() or {}
    modified = cs.update_contract(contract_id, updates)
    return jsonify({"success": True, "data": {"modifiedCount": modified}}), 200


@contract_bp.route("/<string:contract_id>", methods=["DELETE"])
@jwt_required()
def delete_contract(contract_id):
    user_id = get_jwt_identity()
    c = cs.get_by_id_and_user(contract_id, user_id)
    if not c:
        return jsonify({"success": False, "error": "Not found"}), 404
    deleted = cs.delete_contract(contract_id)
    return jsonify({"success": True, "data": {"deletedCount": deleted}}), 200


@contract_bp.route("/<string:contract_id>/detailed", methods=["POST"])
@jwt_required()
def detailed_analysis(contract_id):
    user_id = get_jwt_identity()
    c = cs.get_by_id_and_user(contract_id, user_id)
    if not c:
        return jsonify({"success": False, "error": "Not found"}), 404

    # require file to be uploaded again for detailed analysis (we never store raw)
    if "file" not in request.files:
        return jsonify(
            {
                "success": False,
                "error": "File (docx/pdf) required for detailed analysis. Re-upload the contract file.",
            }
        ), 400

    file = request.files["file"]
    title = c.get("title")
    extracted_text = extract_text_from_file(file)
    if not extracted_text:
        return jsonify(
            {"success": False, "error": "Could not extract text from file."}
        ), 400

    try:
        parsed, raw_xml = agent.detailed_analysis(extracted_text, title=title)
    except RuntimeError as e:
        return jsonify(
            {"success": False, "error": "AI service unavailable", "details": str(e)}
        ), 503
    except ValueError as e:
        return jsonify(
            {
                "success": False,
                "error": "Unable to parse AI response",
                "details": str(e),
            }
        ), 422

    updated = cs.attach_summary_and_set_status(contract_id, parsed, status="detailed")
    out = {
        "id": str(updated["_id"]),
        "title": updated.get("title"),
        "status": updated.get("status"),
        "uploadDate": updated.get("uploadDate"),
        "summary": updated.get("summary"),
    }
    return jsonify({"success": True, "data": out}), 200
