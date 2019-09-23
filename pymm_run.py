#!/usr/bin/python
import argparse
import sched
from flask import redirect
import requests

from matchminer import managment
from matchminer import settings, security
from matchminer.custom import blueprint
from matchminer.database import get_db
from matchminer.events import register_hooks
from matchminer.miner import email_content
from matchminer.utilities import *
from matchminer.validation import ConsentValidatorEve
from services.account import account_pipeline
from eve_swagger import swagger

# logging
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', )

# useful variables
cur_dir = os.path.dirname(os.path.realpath(__file__))
static_dir = os.path.join(cur_dir, 'static')
settings_file = os.path.join(cur_dir, "matchminer/settings.py")


# define the application.
if settings.NO_AUTH:
    logging.warn("NO AUTHENTICATION IS ENABLED")
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


# hot-swappable variables
app.config['SECRET_KEY'] = '2d159b3bd49bc76e93d640f86e46ad29545fc909'
app.config['SAML_PATH'] = os.path.join(cur_dir, 'saml')

# register blueprint to the main Eve application.
app.register_blueprint(blueprint)


app.register_blueprint(swagger)

# API documentation
app.config['SWAGGER_INFO'] = {
    'title': 'Matchminer API',
    'version': '1.0',
    'description': 'Documentation of Matchminer\'s API',
        'termsOfService': 'Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the \"Software\"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software. THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.',
    'contact': {
        'name': 'James Lindsay',
    },
    'license': {
        'name': 'MIT',
        'url': 'https://github.com/pyeve/eve-swagger/blob/master/LICENSE',
    },
    'schemes': ['http', 'https'],
}

# register the springify hook
register_hooks(app)


@app.after_request
def after_request(response):

    # test for response
    is_response, item_id = parse_response(request.url)

    # only redirect if response
    if is_response:

        # do the redirect.
        db = get_db()
        item = db['response'].find_one({"_id": ObjectId(item_id)})

        # if it exists return the redirect.
        if item is not None:
            return make_response(redirect(item['return_url']))

    # remove these headers
    response.headers.add('Last-Modified', datetime.now())
    response.headers.add('Expires', '-1')

    # dont use these headers because IE11 doesn't like them with fonts.
    if response.content_type != 'application/json':
        response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0')
        response.headers.add('Pragma', 'no-cache')

    return response


@app.errorhandler(401)
def my_own_error_msg(err):
    return make_response("unauthorized access", 497)


@app.errorhandler(501)
def redirect_response(err):
    logging.info("redirected to: %s" % err)
    return make_response(redirect(err))


# Generate swagger.io API documentation automatically
@app.before_first_request
def generate_api_docs():
    import json
    try:
        previous_api = json.load(open('./api-swagger-documentation.json'))
        current_api = requests.get(API_ADDRESS + '-docs')
        if not current_api.status_code == 200:
            logging.warn('API documentation request failed - /api-docs')
            return

        if not previous_api == current_api.json():
            new_api = open('api-swagger-documentation.json','w')
            new_api.write(json.dumps(current_api.json()))
            new_api.close()
            logging.info('API changes detected. Successfully generated new swagger documentation => api-swagger-documentation.json')
        else:
            logging.info('No API changes detected. No documentation generated.')
    except:
        logging.warn('Exception occured during API documentation generation. Check that api-swagger-documentation.json exists')


def run_server(args):

    # set enviromental variables.
    os.environ['NO_AUTH'] = str(args.no_auth)

    # start the server
    app.run(host='0.0.0.0', port=settings.API_PORT, threaded=True)


def bootstrap_insert(args):

    # insert default data.
    bootstrap(app, forced=True)


def bootstrap_dump(args):

    # restore the important collections.
    data_dir = settings.DATA_DIR_PROD
    if data_dir == "":
        data_dir = settings.DATA_DIR

    dump_collections(data_dir, settings)


def bootstrap_restore(args):

    # restore the important collections.
    data_dir = settings.DATA_DIR_PROD
    if data_dir == "":
        data_dir = settings.DATA_DIR

    restore_collections(data_dir, settings)

    # fetch the database.
    db = get_db()
    db['clinical'].update_many({"VITAL_STATUS": "dead"}, {"$set": {"VITAL_STATUS": "deceased"}})


def bootstrap_debug(args):

    # add matches.
    bootstrap_matches(app)

    # add simulated structural variants.
    from matchminer.constants import synonyms


def periodic_backup(args):

    # schedule periodic backups
    scheduler = sched.scheduler(time.time, time.sleep)

    # schedule hourly.
    backup_freq = settings.BACKUP_HOURLY_FREQ
    backup_dir = settings.BACKUP_HOURLY_DIR
    max_cnt = settings.BACKUP_HOURLY_MAX
    scheduler.enter(backup_freq, 1, backup_event, (scheduler, backup_dir, backup_freq, max_cnt, False))

    # schedule daily.
    backup_freq = settings.BACKUP_DAILY_FREQ
    backup_dir = settings.BACKUP_DAILY_DIR
    max_cnt = settings.BACKUP_DAILY_MAX
    scheduler.enter(backup_freq, 1, backup_event, (scheduler, backup_dir, backup_freq, max_cnt, False))

    # schedule weekly.
    backup_freq = settings.BACKUP_WEEKLY_FREQ
    backup_dir = settings.BACKUP_WEEKLY_DIR
    max_cnt = settings.BACKUP_WEEKLY_MAX
    scheduler.enter(backup_freq, 1, backup_event, (scheduler, backup_dir, backup_freq, max_cnt, False))

    # run everything.
    scheduler.run()

def account_service(args):

    # schedule periodic backups
    scheduler = sched.scheduler(time.time, time.sleep)

    # schedule the sync.
    scheduler.enter(settings.ACCOUNT_SYNC_FREQ, 1, account_pipeline, (scheduler, settings.ACCOUNT_SYNC_FREQ, -1))

    # run everything.
    scheduler.run()


def manage(args):

    # detect mode.
    if args.mode == "maintain_matches":
        managment.maintain_matches()

    elif args.mode == "maintain_users":
        managment.maintain_users()

    elif args.mode == "maintain_filters":
        managment.maintain_filters()

    elif args.mode == "reannotate_trials":
        managment.reannotate_trials()

    elif args.mode == "maintain_elastic":
        managment.maintain_elastic()


def load_users(args):

    # test insertion.
    insert_users(args.file_path, from_file=True)


def sync_oncologists_email(args):

    # get names.
    names = get_physicians_names()

    # get reference.
    with open(args.file_path) as fin:
        lines = fin.readlines()

    # loop over each name.
    for name_og in names:

        # clean up
        name = name_og.strip().lower()

        # look for hits.
        hits = 0
        tokens = name.split(" ")

        # remove punctuations.
        tokens = [t.replace(".", "").replace("md","").replace(",","") for t in tokens]

        # strip smallies.
        tmp = []
        for t in tokens:
            if len(t) <= 2:
                continue
            tmp.append(t)
        tokens = tmp

        # check ever line.
        for i in range(len(lines) - 2):


            # only do line before email.
            if lines[i+2].count("@") < 1:
                continue

            # clean up.
            line = lines[i].strip().lower()
            email = lines[i+2].strip().lower()

            # match tokens against line.
            hits = 0
            for t in tokens:

                if line.count(t) > 0:
                    hits += 1

            # look for enough hits.
            if hits >= 2:
                xsdf = 1



        #sys.exit()

def sync_oncologists_emailq(args):


    # load the reference.
    ref_df = pd.read_csv(args.file_path, header=0)
    email_lu = {}
    for name, email in zip(ref_df['name'], ref_df['email']):
        if not pd.isnull(email):
            email_lu[name] = email

    # load the oncologists name.
    db = get_db()
    #names = db['clinical'].find().distinct("ORD_PHYSICIAN_NAME")
    names = get_physicians_names()

    # update the database.
    db = get_db()
    clin_cnt = 0
    for name in email_lu:

        # update the clinical records.
        r = db['clinical'].update_many({"ORD_PHYSICIAN_NAME": name}, {"$set": {"ORD_PHYSICIAN_EMAIL": email_lu[name]}})
        clin_cnt += r.modified_count

    logging.info("udpated %d clinical records" % clin_cnt)

    # update all filters.
    genomic_lu = {}
    clinical_lu = {}
    match_cnt = 0
    for filter in db['filter'].find():

        # fix the values.
        protocol_id = ''
        if 'protocol_id' in filter:
            protocol_id = filter['protocol_id']
        email_subject = "(%s) ONCO PANEL RESULTS" % protocol_id

        # loop over each match.
        for match in db['match'].find({"FILTER_ID": ObjectId(filter['_id'])}):

            # do lookup.
            clinical_id = match['CLINICAL_ID']
            genomic_id = match['VARIANTS'][0]

            if clinical_id not in clinical_lu:
                clinical_lu[clinical_id] = db['clinical'].find_one(clinical_id)

            if genomic_id not in genomic_lu:
                genomic_lu[genomic_id] = db['genomic'].find_one(genomic_id)

            # generate body.
            email_body = email_content(protocol_id, genomic_lu[genomic_id], clinical_lu[clinical_id])

            # get name.
            name = clinical_lu[clinical_id]['ORD_PHYSICIAN_NAME']
            email_address = ""
            if name in email_lu:
                email_address = email_lu[name]

            # update all matches.
            db['match'].update_one({"_id": match["_id"]}, {"$set": {
                "EMAIL_ADDRESS": email_address,
                "EMAIL_SUBJECT": email_subject,
                "EMAIL_BODY": email_body,
            }})
            match_cnt += 1

    logging.info("updated %d matches" % match_cnt)

def remove_deceased(args):

    # fetch the database.
    db = get_db()

    # track patients so we don't lookup.
    dead_patients = list(db['clinical'].find({"VITAL_STATUS": "deceased"}))

    logging.info("found %d deceased patients" % len(dead_patients))

    # remove matches for each of these patients.
    match_cnt = 0
    for patient in dead_patients:

        # remove associated matches.
        match_cnt += db['match'].delete_many({"CLINICAL_ID": patient['_id']}).deleted_count

    logging.info("removed %d matches" % match_cnt)


# main
if __name__ == '__main__':

    # mode parser.
    main_p = argparse.ArgumentParser()
    subp = main_p.add_subparsers(help='sub-command help')

    # bootstrap ACC
    subp_p = subp.add_parser('insert', help='adds genomics/clinical to database')
    subp_p.set_defaults(func=bootstrap_insert)

    # dump the data
    subp_p = subp.add_parser('dump', help='serializes data to disk')
    subp_p.set_defaults(func=bootstrap_dump)

    # restore the db.
    subp_p = subp.add_parser('restore', help='restores data from disk')
    subp_p.set_defaults(func=bootstrap_restore)

    # restore the db.
    subp_p = subp.add_parser('debug', help='loads debug data into database')
    subp_p.set_defaults(func=bootstrap_debug)

    # load users from file.
    subp_p = subp.add_parser('load_users', help='loads users from csv file')
    subp_p.add_argument("-f", dest='file_path', type=str, required=True)
    subp_p.set_defaults(func=load_users)

    # backup daemon
    subp_p = subp.add_parser('backup_daemon', help='simple backup daemon')
    subp_p.set_defaults(func=periodic_backup)

    # account daemon
    subp_p = subp.add_parser('account_daemon', help='account sync service')
    subp_p.set_defaults(func=account_service)

    # sync oncologist email (hack)
    subp_p = subp.add_parser('sync_email', help='synchronize oncologist email')
    subp_p.add_argument("-f", dest='file_path', type=str, required=True)
    subp_p.set_defaults(func=sync_oncologists_email)

    # remove matches to decease patients (hack)
    subp_p = subp.add_parser('remove_deceased', help='deletes matches to existing patients')
    subp_p.set_defaults(func=remove_deceased)

    # management scripts.
    subp_p = subp.add_parser('manage', help='managment functions')
    subp_p.add_argument("-m", dest='mode', type=str, required=True)
    subp_p.set_defaults(func=manage)

    # run the webserver.
    subp_p = subp.add_parser('serve', help='runs webserver')
    subp_p.add_argument("-d", dest='debug', action='store_const', const=True, default=False)
    subp_p.add_argument("--no-auth", dest='no_auth', action='store_const', const=True, default=False)
    subp_p.set_defaults(func=run_server)

    # parse args.
    args = main_p.parse_args()
    args.func(args)
