from flask import (
    render_template,
    request,
    render_template,
    flash,
    redirect,
    url_for,
    Blueprint,
    current_app,
    session,
)
import modules.cert.readwrite
import modules.cert.checkexpiry
from modules.authentication import validate_user_role
import logging
import json

cert_blueprint_routes = Blueprint(
    "cert_blueprint_routes",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="cert",
)

logging.getLogger().setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logging.captureWarnings(True)
#LEVEL="DEBUG"
#logging.getLogger().setLevel(eval("logging." + LEVEL))
logging.info("This is from %s and is a INFO message" % __name__)
logging.debug("This is from %s and is a DEBUG message" % __name__)
logging.warn("This is from %s and is a WARNING message" % __name__)

@cert_blueprint_routes.route("/")
def index():
    try:
        session["username"]
    except:
        flash("Not logged in", "info")
        return redirect(url_for("login_blueprint_routes.login"))

    logging.debug("This is @cert_blueprint_routes.index()")
    results = request.args.get("cert")
    certs = modules.cert.readwrite.read_records_db()
    return render_template("cert/index.html", results=results, certs=certs)


@cert_blueprint_routes.route("/add", methods=["GET", "POST"])
def add():
    if not validate_user_role(session["username"], session["role"], "admin"):
        flash(f'Your user {session["role"]} is not authorised to add users', "warning")
        return redirect(url_for("cert_blueprint_routes.index"))
    cert = {}
    addhelp={}
    if request.method == "POST":
        try:
            cert["url"] = request.form["url"]
        except:
            pass
        try:
            cert["port"] = request.form["port"]
        except:
            pass
        try:
            cert["contact"] = request.form["contact"]
        except:
            pass
        addhelp={}
        if ( not request.form["url"] ):
            addhelp["url"]="*"
        if ( not request.form["port"] ):
            addhelp["port"] = "*"
        if (
                not request.form["url"]
                or not request.form["port"]
                or not request.form["contact"]
        ):
            flash("Please enter all the fields", "warning")
            return render_template("cert/add.html", cert=cert,addhelp=addhelp)
        else:
            cert = {
                "url": request.form["url"],
                "port": request.form["port"],
                "contact": request.form["contact"],
            }
            try:
               daysToGo,expiryDate = modules.cert.checkexpiry.checkcert(cert)
               cert['daysToGo']=daysToGo
               cert['expiryDate']=expiryDate
            except:
               daysToGo  = -1
            if modules.cert.readwrite.insert_record_db(cert):
                flash("Record was successfully added", 'success')
            else:
                flash(f"Record {cert} was not added", 'warning')
            return redirect(url_for("cert_blueprint_routes.index"))
    return render_template("cert/add.html",cert=cert,addhelp=addhelp)


@cert_blueprint_routes.route("/search", methods=["GET"])
def search():
    cert={}
    try:
        request.args.get('url')
        cert['url'] = request.args.get('url') 
    except: 
        flash("Please enter a url search string", "info")
        return redirect(url_for("cert_blueprint_routes.index"),url=None,port=port)
    if request.args.get('port'):
        cert['port'] = request.args.get('port') 
    else:
        cert['port'] = "443"
    result = modules.cert.readwrite.read_record_db(cert)
    if len(result) == 1:
        pass
        logging.debug(f"Record found {cert}")
    elif len(result) > 1:
        flash(f"Multiple records found for {cert['url']}", "warning")
    elif len(result) == 0:
        flash("Not found", "info")
        result = {}
    certs = modules.cert.readwrite.read_records_db()
    return render_template("cert/index.html", result=result, certs=certs)


@cert_blueprint_routes.route("/edit", methods=["GET", "POST"])
def edit():
    if request.method == "GET":
        cert = { "url": request.args.get("url"), 
             "port": request.args.get("port"),
             "contact": request.args.get("contact")
            }
    if request.method == "POST":
        cert= {
            "url": request.form["url"],
            "port": request.form["port"],
            "contact": request.form["contact"]
        }
        try:
            request.form["update_button"]
            if request.form["update_button"] == "update_button":
                logging.debug("About to update")
                logging.debug(f"About to update {cert}")
                if modules.cert.readwrite.update_record_db_ext(cert):
                    logging.warning("ran the update %s" % cert)
                    flash(f"Record {cert['url']} was updated ", 'info')
                else:
                    logging.debug("failed the update db_ext")
                    flash(f"Error {cert['url']} was not updated", 'error')
        except:
            pass
    return render_template("cert/edit.html", cert=cert)


@cert_blueprint_routes.route("/delete", methods=["POST"])
def delete():
    cert = {
        "url": request.form["url"],
        "port": request.form["port"],
    }
    try:
        request.form["delete_button"]
        if request.form["delete_button"] == "delete_button":
            logging.debug("About to delete %s" % cert )
            if modules.cert.readwrite.delete_record_db(cert):
                flash(f"certificate record for {cert['url']}:{cert['port']} was deleted", "warning")
            else:
                logging.debug("failed to delete %s " % cert)
                flash(f"Error {cert['url']} failed to delete", "danger")
    except:
        pass
        print("request.form.delete ", request.form["delete"])
        flash("Failed to delete")
    return redirect(url_for("cert_blueprint_routes.index", cert=cert))

@cert_blueprint_routes.route("/check", methods=["POST"])
def check():
    logging.getLogger().setLevel(logging.DEBUG)
    cert = {
        "url": request.form["url"],
        "port": request.form["port"]
    }
    if request.form["check_button"] == "check_button":
            try:
               daysToGo,expiryDate = modules.cert.checkexpiry.checkcert(cert)
            except:
                logging.debug('failed to call checkexpiry')
                flash('Failed to check')
                return redirect(url_for("cert_blueprint_routes.index", cert=cert))
            if daysToGo >=0:
                 cert['status'] = "up"
                 cert['expiryDate'] = expiryDate
            else:
                 cert['status'] = "down"
            cert['daysToGo'] = daysToGo
            if modules.cert.readwrite.update_record_db_ext(cert):
                 logging.warning("ran the update %s" % cert)
                 flash(f"Record {cert['url']} was updated ", 'info')
            else:
                 logging.debug("failed the update db_ext")
                 flash(f"Error {cert['url']} was not updated", 'error')
    return redirect(url_for("cert_blueprint_routes.search", url=cert["url"], port=cert["port"]))

@cert_blueprint_routes.route("/checkall", methods=["POST"])
def checkall():
    logging.getLogger().setLevel(logging.DEBUG)
    modules.cert.readwrite.recalculateAll()
    return redirect(url_for("cert_blueprint_routes.index" ))
