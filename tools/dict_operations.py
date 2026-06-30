# A part of MC Code Copier Reloaded
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# File contains flatten_dict and flatten_values functions
# Function that can escape recursive dicts
def flatten_dict(d:dict,parent_key:str="",separator:str=".")->dict:
	result={}
	for key,value in d.items():
		full_key=f"{parent_key}{separator}{key}"if parent_key else key
		if isinstance(value,(list,tuple)):
			readval=dict(enumerate(value))
		else:
			readval=value
		if isinstance(readval,dict):
			nested_dicts={}
			for k,v in readval.items():
				if isinstance(v,dict):
					nested_dicts[k]=v
			flat_values={}
			for k,v in readval.items():
				if not isinstance(v,dict):
					if isinstance(v,(list,tuple)):
						nested_dicts[k]=dict(enumerate(v))
					else:
						flat_values[k]=v
			if flat_values:
				result[full_key]=flat_values
			if nested_dicts:
				nested_result=flatten_dict(nested_dicts,full_key,separator)
				result.update(nested_result)
		else:
			result[key]=value
	return result
# Function to return flatten values
def flatten_values(d:dict)->dict:
	result={}
	flattened=flatten_dict(d=d)
	for key,value in flattened.items():
		if isinstance(value,dict):
			for k,v in value.items():
				result[f"{key}.{k}"]=v
		else:
			result[key]=value
	return result