import servicenow_client 


obj = servicenow_client.servNow(instance='nordstrom', 
	                           user='api0046.prod.user', 
	                           password='<redacted>', 
	                           empty_error=True)

print(obj.search(table='incident', 
	       searchList=['number','is','CHG0000017557'])) 

# Search for record(s) and display only 'number' and 'sys_id' from the results 
# if fields is not defined it will return all fiels in response 
# obj.search(table='incident', 
# 	       searchList=['short_description','is not empty'], 
# 	       fields='number,sys_id') 

# Update record(s) based on search condition 
# searchList=['field', 'operator', 'value'] 
# obj.update(table='incident', 
# 	       searchList=[['short_description','is','My Incident Ticket'], 
# 	                   ['number','is not','INC0010022']], 
# 	       data={'state': '1'}) 
