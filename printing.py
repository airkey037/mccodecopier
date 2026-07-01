# A part of MC Code Copier Reloaded
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# File contains Printing class that manages print formats
# Import needed modules
import logging
from tools import flatten_dict, flatten_values
# Declare required functions
# Function to escape " and ' in strings
def escape_flat(s:str)->str:return(str(s).replace("\\","\\\\").replace('"','\\"').replace("'","\\'"))
# Class to manage print format and additional printed info
class Printing:
    def parser_default(self)->str:
        self.logger.debug("Parsing mode: default")
        def default_pf(tree,prefix:str="",use_brackets=True)->tuple:
            pfx=f"{prefix}:"if prefix else""
            output=[]
            rv=tree
            if isinstance(tree,(list,tuple)):
                rv=dict(enumerate(tree))
            if isinstance(rv,dict):
                for key,value in rv.items():
                    usebrk=use_brackets and isinstance(value,(list,dict,tuple))
                    if usebrk:
                        output.append(f"[{str(key).upper()}]")
                    output.extend(default_pf(value,prefix=f"{pfx}{key}",use_brackets=False))
                    if usebrk:
                        output.append(f"[/{str(key).upper()}]")
            else:
                output.append(f"{prefix}={rv}")
            return tuple(output)
        return "\n".join(default_pf(self.tree))
    def parser_flat(self)->str:
        self.logger.debug("Parsing mode: flat")
        el_list=[]
        escaped=flatten_values(self.tree)
        for k,v in escaped.items():
            el_list.append(f"{escape_flat(k)}=\"{escape_flat(v)}\"")
        return "\n".join(el_list)
    def parser_ini(self)->str:
        self.logger.debug("Parsing mode: ini")
        from configparser import ConfigParser
        from io import StringIO
        config=ConfigParser()
        escaped=flatten_dict(self.tree)
        for key,value in escaped.items():
            config[key]=value
        buf=StringIO()
        config.write(buf)
        return buf.getvalue().strip()
    def parser_json(self)->str:
        self.logger.debug("Parsing mode: json")
        from json import dumps
        return dumps(self.tree)
    def parser_xml(self)->str:
        self.logger.debug("Parsing mode: xml")
        import xml.etree.ElementTree as ET
        def dict_to_xml(data:dict,root_tag:str="root")->str:
            def build_element(parent:ET.Element,key:str,value):
                if isinstance(value,dict):
                    child=ET.SubElement(parent,key)
                    for k,v in value.items():
                        build_element(child,k,v)
                elif isinstance(value,(list,tuple)):
                    container=ET.SubElement(parent,key)
                    for item in value:
                        if isinstance(item,dict):
                            el=ET.SubElement(container,"item")
                            for k,v in item.items():
                                build_element(el,k,v)
                        else:
                            el=ET.SubElement(container,"item")
                            el.text=str(item)
                elif isinstance(value,(int,float,str,bool)):
                    parent.set(key,str(value))
                else:
                    parent.set(key,repr(value))
            root=ET.Element(root_tag)
            for key,value in data.items():
                build_element(root,key,value)
            ET.indent(root,space="  ")
            return ET.tostring(root,encoding="unicode",xml_declaration=True)
        return dict_to_xml(data=self.tree,root_tag="codecopy")
    def __init__(self,print_format:str="default"):
        # Get class-level logger
        self.logger=logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        # Define all parsers
        self.parsers={"default":self.parser_default,"flat":self.parser_flat,"ini":self.parser_ini,"json":self.parser_json,"xml":self.parser_xml}
        self.logger.debug("Checking print_format type")
        if type(print_format)is str:
            self.logger.debug("print_format is str; checking, is it correct format name")
            if print_format in self.parsers.keys():
                self.logger.debug(f"{print_format} is correct parser name, using this format's parser")
                self.using_parser=self.parsers[print_format]
            else:
                raise KeyError(f"{print_format} isn't correct print format! Allowed formats: {", ".join(self.parsers.keys())}")
        else:
            raise TypeError(f"print_format have to be str, not {print_format.__class__.__name__}!")
        self.tree={}
    def add_element(self,name:str,tree:dict):
        self.logger.debug("Checking is name a string")
        if type(name)is str:
            self.logger.debug("name is string; checking, is this element already in main tree")
            if name in self.tree.keys():
                raise FileExistsError(f"{name} is already added to main tree!")
            self.logger.debug(f"{name} doesn't exist in main tree! Checking, is given tree a dict, list or tuple")
            if isinstance(tree,(dict,list,tuple)):
                self.logger.debug(f"tree is {tree.__class__.__name__}, adding element to the main tree! Name: {name}; Tree: {tree}")
                self.tree[name]=tree
            else:
                raise TypeError(f"tree have to be dict, list or tuple, not {tree.__class__.__name__}!")
        else:
            raise TypeError(f"name have to be str, not {name.__class__.__name__}!")
    def parse(self):
        self.logger.debug("Parsing all elements using specified parser")
        self.logger.debug(f"Using parser: {self.using_parser.__name__}")
        return self.using_parser()