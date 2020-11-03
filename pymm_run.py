#!/usr/bin/python
import argparse
from eve import Eve
from flask import redirect
from eve_swagger import swagger

from matchminer.elasticsearch import reset_elasticsearch
from matchminer.utilities import *
from matchminer.custom import blueprint
from matchminer import settings, security
from matchminer.events import register_hooks
from matchminer.validation import ConsentValidatorEve
from matchminer.components.oncore.oncore_app import oncore_blueprint

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s', )

cur_dir = os.path.dirname(os.path.realpath(__file__))
static_dir = os.path.join(cur_dir, 'static')
settings_file = os.path.join(cur_dir, "matchminer/settings.py")

if settings.NO_AUTH:
    logging.warning("NO AUTHENTICATION IS ENABLED - SKIPPING HIPAA LOGGING")
    app = Eve(settings=settings_file,
              static_folder=static_dir,
              static_url_path='',
              validator=ConsentValidatorEve)
else:
    app = Eve(settings=settings_file,
              static_folder=static_dir,
              static_url_path='',
              auth=security.TokenAuth,
              validator=ConsentValidatorEve)

app.config['SAML_PATH'] = os.path.join(cur_dir, 'saml')
app.config['SECRET_KEY'] = SAML_SECRET
app.config['SWAGGER_INFO'] = SWAGGER_INFO
app.register_blueprint(blueprint)
app.register_blueprint(oncore_blueprint)
app.register_blueprint(swagger)
register_hooks(app)


@app.after_request
def after_request(response):
    # dont use these headers because IE11 doesn't like them with fonts.
    if response.content_type != 'application/json':
        response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0')
        response.headers.add('Pragma', 'no-cache')

    return response


@app.errorhandler(401)
def error_handle_401(err):
    return make_response("unauthorized access", 497)


@app.errorhandler(501)
def redirect_response(err):
    logging.info("redirected to: %s" % err)
    return make_response(redirect(err))


def run_server(args):
    os.environ['NO_AUTH'] = str(args.no_auth)
    app.run(host='0.0.0.0', port=settings.API_PORT, threaded=True)


# main
if __name__ == '__main__':
    main_p = argparse.ArgumentParser()
    subp = main_p.add_subparsers(help='sub-command help')

    subp_p = subp.add_parser('serve', help='runs webserver')
    subp_p.add_argument("-d", dest='debug', action='store_const', const=True, default=False)
    subp_p.add_argument("--no-auth", dest='no_auth', action='store_const', const=True,
                        default=False)
    subp_p.set_defaults(func=run_server)

    subp_p = subp.add_parser('reset-elasticsearch', help='resets elasticsearch')
    subp_p.set_defaults(func=lambda x: reset_elasticsearch())

    subp_p = subp.add_parser('reannotate-trials', help='regenerates elasticsearch fields on all trials')
    subp_p.set_defaults(func=lambda x: reannotate_trials())

    args = main_p.parse_args()
    args.func(args)
