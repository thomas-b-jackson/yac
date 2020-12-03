from yac.lib.module import get_module

class CustomDriver():

    def __init__( self,
                 test_name,
                 target,
                 driver_path,
                 test_results,
                 params,
                 context ):

        self.test_name = test_name
        self.target = target
        self.driver_path = driver_path
        self.test_results = test_results
        self.params = params
        self.context = context

    def run( self ):

        servicefile_path = self.params.get("servicefile-path")

        module, err = get_module(self.driver_path, 
                                 servicefile_path)

        if not err:

            if hasattr(module,'test_driver'):

                # call the test driver fxn in the module
                return_val = module.test_driver( self.test_name,
                                                 self.target,
                                                 self.test_results,
                                                 self.params,
                                                 self.context)
            else: 

                msg = ("custom test module %s does  " +
                       "not have a 'test_driver' function"%self.driver_path)

        if err:
            self.test_results.failing_test(self.test_name, err)