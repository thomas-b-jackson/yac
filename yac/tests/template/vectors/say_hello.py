def do_calc(argv, params):
    # say hello to anyone in argv

    if argv and len(argv)==1:
    	return "hello %s"%argv[0], ""
    else:
    	return "hello stranger", ""
