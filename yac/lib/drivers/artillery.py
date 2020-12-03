import sys, os, glob, json, subprocess, jmespath, random, datetime
from yac.lib.intrinsic import apply_intrinsics
from yac.lib.search import search
from yac.lib.paths import get_dump_path

class ArtilleryDriver():

    def __init__( self,
                 test_name,
                 target,
                 artillery_descriptor,
                 test_results,
                 params ):

        self.test_name = test_name
        self.target = target
        self.config_path = search('config',artillery_descriptor,"")
        self.test_assertions = search('assertions',artillery_descriptor,{})
        self.variables = search('variables',artillery_descriptor,{})
        self.test_results = test_results
        self.params = params
        self.artillery_aggregates = {}

    def run( self ):

        # render variables in the artillery variables
        apply_intrinsics(self.variables,self.params)

        variables_str = ""

        if self.variables:
            # render variables into a string
            # note: need to make sure no whitespace chars are included
            variables_str = "-v '%s'"%json.dumps(self.variables,separators=(',', ':'))

        results_path = self.get_results_path()

        # from the artillery command
        artillery_cmd = "artillery run %s %s -k -t %s -o %s"%( self.config_path,
                                                               variables_str,
                                                               self.target,
                                                               results_path )

        print("artillery command:\n{0}".format( artillery_cmd ))

        process = subprocess.Popen( artillery_cmd,
                                    shell=True,
                                    stdout=subprocess.PIPE )

        while True:
            line = process.stdout.readline()
            if line != b'':
                os.write(1, line)
            else:
                break

        # load results
        results_dict = load_dictionary( results_path )

        if self.test_name in self.artillery_aggregates:

            print("name collision: %s is already included in test results"%self.test_name)
            self.test_name = "%s-%s"%(self.test_name,random.randint(1,10))
            print("saving results as %s"%self.test_name)

        # initiate results for this test
        self.artillery_aggregates[self.test_name] = {}

        # save the aggregates
        if 'aggregate' in results_dict:

            self.artillery_aggregates[self.test_name] = results_dict['aggregate']

        # register results file
        self.test_results.append_results_file( results_path )

        # run assertions
        self.assert_results()

    def assert_results( self ):

        for assertion_key in list(self.test_assertions.keys()):

            if assertion_key == 'p95_sec':

                # assert p95 latency
                value_ms = self.get_p95()

                if value_ms:

                    value_sec = value_ms/1000
                    threshold_sec = float(self.test_assertions[assertion_key])
                    threshold_ms = 1000*threshold_sec

                    if value_ms > threshold_ms:

                        # fail the test and break out of the assertion loop
                        msg = ("p95 latency exceeded threshold\n" +
                         "measured: %s, threshold: %s"%(value_sec,threshold_sec) )
                        self.test_results.failing_test(self.test_name,msg)
                        passing = False
                        break

                else:

                    msg = ("p95 latency is null, so test deemed a failure. \n" +
                           "increase test duration?" )
                    self.test_results.failing_test(self.test_name, msg)
                    break

            if assertion_key == 'median_sec':

                # assert median latency
                value_ms = self.get_median()

                if value_ms:

                    value_sec = value_ms/1000
                    threshold_sec = float(self.test_assertions[assertion_key])
                    threshold_ms = 1000*threshold_sec

                    if value_ms > threshold_ms:

                        msg = ("median latency exceeded threshold\n" +
                         "measured: %s, threshold: %s"%(value_sec,threshold_sec) )
                        self.test_results.failing_test(self.test_name,msg)
                        break

                else:

                    msg = ("median latency is null, so test deemed a failure. \n" +
                           "connectivity problem?" )
                    self.test_results.failing_test(self.test_name, msg)
                    break

            if assertion_key == 'errors':

                # assert error counts
                error_count = self.get_errors()
                threshold_count = self.test_assertions[assertion_key]

                if (error_count and error_count > threshold_count):

                    msg = ("error count exceeded threshold\n" +
                     "measured: %s, threshold: %s"%(error_count,threshold_count) )
                    self.test_results.failing_test(self.test_name,msg)
                    break

            if assertion_key == 'status':

                # assert status codes
                status_codes_set = set(self.get_codes())

                assertion_codes_set = set(self.test_assertions[assertion_key])

                # assert that only the assertion codes are represented in the
                # status codes returned.
                if status_codes_set.difference(assertion_codes_set):

                    msg = ("status codes assertion failed.\n" +
                     "measured: %s, assertion: %s"%(status_codes_set,assertion_codes_set) )
                    self.test_results.failing_test(self.test_name,msg)
                    break

        # if made it through all assertions with no failures, record a passing
        if self.test_name not in self.test_results.get_failing_tests():
            self.test_results.passing_test(self.test_name)

    def create_config_file(self):

        # save config file under /tmp
        configs_path = os.path.join('/tmp','%s.json'%self.test_name)

        write_dictionary(self.test_description, configs_path)

        return configs_path

    def get_results_path(self):

        timestamp = "{:%Y-%m-%d.%H.%M.%S}".format(datetime.datetime.now())

        # save results a consistent path
        dump_path = get_dump_path(self.params.get("service-alias"))

        results_path = os.path.join(dump_path,'%s.%s'%(self.test_name,timestamp))

        if not os.path.exists(dump_path):
            os.makedirs(dump_path)

        return results_path

    def load_results(self):

        results_file_search_str = "results/%s.%s.*"%(test_name,env)

        # find all results from this env
        all_results = list(filter(os.path.isfile, glob.glob(results_file_search_str)))

        # sort in ascending order
        all_results.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        self.most_recent_results = {}

        # record the latest results file later use
        if (len(all_results)>=1):

            self.most_recent_results = load_dictionary(all_results[0])

    # get codes
    def get_codes(self):
        # get http status codes
        return jmespath.search("codes",self.artillery_aggregates[self.test_name])

    # get 95th percentile
    def get_p95(self):

        # per https://artillery.io/docs/getting-started/ ...
        #   Request latency and Scenario duration are in milliseconds, and p95 and p99
        #   values are the 95th and 99th percentile values (a request latency p99 value of
        #   500ms means that 99 out of 100 requests took 500ms or less to complete)

        return jmespath.search("latency.p95",self.artillery_aggregates[self.test_name])

    # get median lantency
    def get_median(self):

        return jmespath.search("latency.median",self.artillery_aggregates[self.test_name])

    # get errors from the most recent test run
    def get_errors(self):

        return jmespath.search("errors",self.artillery_aggregates[self.test_name])

    # get count of non-HTTP 2xx status codes from the
    # most recent test run
    def get_bad_http_status_counts(self):

        return get_bad_http_status_counts(self.artillery_aggregates[self.test_name])

# get count of non-HTTP 2xx status codes from the
# most recent test run
def get_bad_http_status_counts(results_dict):

    codes = jmespath.search("codes",results_dict)

    bad_status_count=0
    if codes:
        for code in codes:
            if code not in ["200","201"]:
                bad_status_count+=codes[code]

    return bad_status_count

def load_dictionary(file_path):

    dictionary = {}

    if os.path.exists(file_path):

        with open(file_path) as file_path_fp:

            file_contents = file_path_fp.read()

            dictionary = json.loads(file_contents)

    return dictionary

def write_dictionary(dict, file_w_path):

    dict_str = json.dumps(dict, indent=2)

    file_path = os.path.dirname(file_w_path)

    if not os.path.exists(file_path):

        os.makedirs(file_path, exist_ok=True)

    with open(file_w_path,'w') as file_path_fp:

        file_path_fp.write(dict_str)
