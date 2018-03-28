#!/usr/bin/python

import csv

from flask import Flask, abort, request
app = Flask(__name__)

class EligibilityCheck():
    def __init__(self, customer):
        self.customer = customer
        self.strategy = customers[customer]['strategy']
        self.required_fields = customers[customer]['required_fields']

        self.eligibile_employees = {}
        if self.strategy['type'] == 'tsv_file':
            # Pre-load from file
            required_field_columns = [x[1] for x in self.required_fields]
            with open(self.strategy['file_path'], 'r') as csvfile:
                reader = csv.reader(csvfile, delimiter='\t')
                for row in reader:
                    eligibility_key = []
                    for column in required_field_columns:
                        eligibility_key.append(row[column])
                    self.eligibile_employees['|'.join(eligibility_key)] = True
        elif self.strategy['type'] == 'remote_json':
            # Check will be done in real-time
            # Not implemented yet
            pass
        elif self.strategy['type'] == 'mysql_database':
            # Similar to reading from a TSV file
            # Not implemented yet
            pass
        else:
            # Should never get here
            print "Unknown eligibility check strategy \'{}\'".format(self.strategy['type'])
            abort(500)

    def __repr__(self):
        return "EligibilityCheck({})".format(self.customer)
    
    def __str__(self):
        return "EligibilityCheck({} req:{} strat:{})".format(self.customer, self.required_fields, self.strategy)
    
    def config(self):
        return [x[0] for x in self.required_fields]

    def check(self, params):
        error_message = "No error"

        if self.strategy['type'] == 'tsv_file':
            key = '|'.join(params)
            if key in self.eligibile_employees:
                return '{"eligible": true, "message": ""}'
            else:
                return '{"eligible": false, "message": "Could not find \'%s\' in eligibility list for customer %s -- expecting fields %s"}' % (key, self.customer, str([x[0] for x in self.required_fields]))
        elif self.strategy['type'] == 'mysql_database' or self.strategy['type'] == 'remote_json':
            # Not implemented yet
            abort(501)
        else:
            abort(500)

    def validate(self, fields):
        # todo - add data type checks
        return len(fields) == len(self.required_fields)
        
# This could be stored in a datastore of some kind, keeping it here
# for transparency
customers = {'acme': {'required_fields': [['employee_id', 0]],
                      'optional_fields': ['first_name', 'last_name', 'start_date'],
                      'strategy': {'type': 'tsv_file',
                                   'file_path': '/home/eisen/JobSearch2018/GenomeMedical/EligibilityChallenge/data.tsv'}},
             'yoyodyne': {'required_fields': {'firstname': 'string', 'lastname': 'string'},
                          'strategy': {'type': 'remote_json',
                                       'url': 'http://api.blue_sun.com/employee?firstname=%s&lastname=%s'}},
             'pied_piper': {'required_fields': [['first_name', 0], ['last_name', 1]],
                            'optional_fields': ['employee_id', 'start_date'],
                            'strategy': {'type': 'mysql_database',
                                         'connection_string': 'server=192.168.10.20;uid=public_api;pwd=12345;database=genome_medical',
                                         'table': 'eligibility'}}}


# If I had more time for a larger, more permanent project, this would
# not be global, but it's the easiest/fastest way to get something
# working for the Flask microframework.
EligibilityChecks = {}
for customer in customers:
    EligibilityChecks[customer] = EligibilityCheck(customer)

@app.route("/v1/ping")
def ping():
    return "Pong"

@app.route("/v1/config/<string:customer>")
def config(customer):
    print customer
    if customer in customers:
        return str(EligibilityChecks[customer].config())
    else:
        return "{'error': 'Customer \'%s\' not found'}" % (customer)

@app.route("/v1/check/<string:customer>", methods=['POST'])
def check(customer):

    if customer not in customers:
        return "{'error': 'Customer \'%s\' not found'}" % (customer)

    eligibility_check = EligibilityChecks[customer]
    fields = []
    
    for required_field in eligibility_check.config():
        if request.form[required_field] is not None:
            fields.append(request.form[required_field])

    if eligibility_check.validate(fields):
        return eligibility_check.check(fields)
    else:
        abort(400)

@app.route("/v1/customers")
def list_customers():
    return str(customers.keys())

@app.route("/")
def usage():
    return """
<html>
 <head>
  <title> Genome Medical - Eligibility Challenge </title>
 </head>
 <body>
  <h1> Usage </h1>
  <div>
   <ul>
    <li> GET /v1/ping - test that the server is up </li>
    <li> GET /v1/customers - list customers currently configured </li>
    <li> GET /v1/config/CUSTOMER - must provide a valid customer name </li>
    <li> POST /v1/check/CUSTOMER - must provide a valid customer name, and fields in the POST form as per the config for that customer </li>
   </ul>
  </div>
 </budy>
</html>
"""
