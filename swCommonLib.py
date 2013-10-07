#
# Copyright 2013 Plexxi, Inc.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# @author: Simon McCormack, Plexxi Systems, Inc.
# @author: Austin Xu, Plexxi Systems, Inc.
#

global DEBUG
DEBUG = 0 

def processArgs(args):
	ar={}
	for key, value in args:
		ar[key]=value
	return ar


def argChecker(required,optional,items):
	ar=processArgs(items)
	opt=optionaAttribute(optional,ar)
	if not requiredAttribute(required,ar):
		return False
	else:
		return dict(ar.items() + opt.items())

def optionaAttribute(attr,lst):
	ar={}
	for Attr in attr:
		if Attr not in lst:
			ar[Attr]=None
	return ar

def requiredAttribute(attr,lst):
	for Attr in attr:
		if Attr not in lst:
			print "%s is a required attribute"%(Attr)
			print "Called from %s()"%(inspect.stack()[2][3])
			return False
	return True

def debugPrint(msg):
	global DEBUG
	if DEBUG:
		print msg
	if DEBUG == 2:
		print "---------- Stack Start --------"
		print traceback.print_stack(file=sys.stdout)
		print "---------- Stack End ----------"


def convertSQLtoREST(data):
  # convert data string to REST format put in dataString
	newStr = data.replace(", ","+,+")
	newStr2 = newStr.replace(" ","+")
	return newStr2


def getFieldList(data):

	dataList = data.replace("SELECT ","")
	dataList2 = dataList.replace(" FROM","")
	dataList2 = dataList2.replace(",","")
	dataList3 = str.split(dataList2)
	size = len(str.split(dataList2))
	variable = (str.split(dataList2)[size-1])

	dataList2A = dataList2.replace(variable,"")
	dataList4 = str.split(dataList2A) 
	return dataList4


def convertFieldListToSelect(fieldList, tableName):

	output = 'SELECT+'
	for field in fieldList:
		output = output + field
		output = output + '+,+'
	output = output + 'FROM+'
	output = output + tableName
	output = output.replace(',+,+','+,+')
	output = output.replace(',+FROM','FROM')
	return output

def convertSelectListToSelect(fieldList, tableName, selectList):

	if any((False for x in selectList if x in fieldList)):
		print 'error', selectList, fieldList
		return 0

	output2 = 'SELECT+'
	for field in selectList:
		output2 = output2 + field
		output2 = output2 + '+,+'
	output2 = output2 + 'FROM+'
	output2 = output2 + tableName
	output2 = output2.replace(',+FROM','FROM')
	return output2


def convertWhereListToWhere(fieldList, tableName, whereList):
	if any((False for x in whereList if x in fieldList)):
		print 'FieldList error', whereList
		return 0
	output3 = 'SELECT+'
	for field in fieldList:
		output3 = output3 + field
		output3 = output3 + '+,+'
	output3 = output3 + 'FROM+'
	output3 = output3.replace(',+FROM','FROM')
	output3 = output3 + tableName
	output4 = '+WHERE+'
	for field in whereList:
		output4 = output4 + field
		output4 = output4 + '+'
	output3 = output3 + output4
	output3 = output3.replace(',+FROM','FROM')
	output3 = output3 + '=+'
	value = whereList[field]
	if type(value) is int:
		output3 = output3 + str(whereList[field])
	else:
		output3 = output3 + '%27' + whereList[field] + '%27'
	output3 = output3.replace(',+,+','+,+')
	return output3

def convertSelectWhereListToSelectWhere(fieldList, tableName, selectList, whereList):

	if any((False for x in selectList if x in fieldList)): 
		print 'FieldList error', selectList, whereList
		return 0
	if any((False for x in whereList if x in fieldList)):
		print 'FieldList error', selectList, whereList
		return 0
	output3 = 'SELECT+'
	for field in selectList:
		output3 = output3 + field
		output3 = output3 + '+,+'
	output3 = output3 + 'FROM+'
	output3 = output3 + tableName
	output4 = '+WHERE+'
	for field in whereList:
		output4 = output4 + field
		output4 = output4 + '+'
	output3 = output3 + output4
	output3 = output3 + '=+'
	value = whereList[field]
	if type(value) is int:
		output3 = output3 + str(whereList[field])
	else:
		output3 = output3 + '%27' + whereList[field] + '%27'
	output3 = output3.replace(',+FROM','FROM')
	output3 = output3.replace(',+,+','+,+')

	return output3

def getTableName(data):
	data = str(data)
	data2 = data.split("FROM ")[1]

	return data2

def getClassName(data):
	data = str(data)
	data2 = data.split("FROM ")[1]
	data2 = data2.replace('.','')

	return data2

def getFunctionName(data):
	data = str(data)
	data2 = data.split("FROM ")[1]
	data2 = data2.replace('.','')
	func = lambda s: s[:1].lower() + s[1:] if s else ''
	data2 = func(data2)

	return data2

###########################################################################

def helperPrint(data, fileHandle=None):
	print data
	fileHandle.append(data)

def helper(data, classFile, outFile, otherFile):
	swSelect = convertSQLtoREST(data)
# get the name of the class from the FROM field so for example Orion.VIM.VMStatstics = vimVMStatistics
	swClassName = getClassName(data)
	swFunctionName = getFunctionName(data)
	swFieldList = getFieldList(data)
	swTableName = getTableName(data)

	helperPrint ("\n\tdef get%s(self,**kwargs):\n"%swClassName, outFile)
	helperPrint ("\t\trequiredArgs=[]\n", outFile)
	helperPrint ("\t\toptionalArgs=['selectList', 'whereList']\n", outFile)
	helperPrint ("\t\tar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())\n", outFile)
	helperPrint ("\t\tself.%sObjs=[]\n"%swFunctionName, outFile)
	helperPrint ("\t\tself.selectList=ar['selectList']\n", outFile)
	helperPrint ("\t\tself.whereList=ar['whereList']\n", outFile)
	helperPrint ("\t\tfieldList = %s\n"%swFieldList, outFile)
	helperPrint ("\t\ttableName = '%s'\n"%swTableName, outFile)
	helperPrint ("\t\tselectQuery = None\n", outFile)
	helperPrint ("\t\tif not ar['selectList'] and not ar['whereList']:\n", outFile)
	helperPrint ("\t\t\tselectQuery = convertFieldListToSelect(fieldList, tableName)\n", outFile)
	helperPrint ("\t\telif ar['selectList'] and not ar['whereList']:\n", outFile)
	helperPrint ("\t\t\tselectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])\n", outFile)
	helperPrint ("\t\telif not ar['selectList'] and ar['whereList']:\n", outFile)
	helperPrint ("\t\t\tselectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])\n", outFile)
	helperPrint ("\t\telif ar['selectList'] and ar['whereList']:\n", outFile)
	helperPrint ("\t\t\tselectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])\n", outFile)
	helperPrint ("\t\tif selectQuery:\n", outFile)
	currStr = "curr%s"%swClassName
	helperPrint ("\t\t\t%s = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)\n"%currStr, outFile)
	helperPrint ("\t\t\tif %s == None:\n"%currStr, outFile)
	helperPrint ("\t\t\t\treturn []\n", outFile)
	helperPrint ("\t\tfor obj in %s['results']:\n"%currStr, outFile)
	helperPrint ("\t\t\tthisObj = %s(connection=self,data=obj)\n"%swClassName, outFile)
	helperPrint ("\t\t\tself.%sObjs.append(thisObj)\n"%swFunctionName, outFile)
	helperPrint ("\t\treturn self.%sObjs\n"%swFunctionName, outFile)

	helperPrint ("\nclass %s():\n"%swClassName, otherFile)
	helperPrint ("\n\tdef __init__(self,**kwargs):\n", otherFile)
	helperPrint ("\t\trequiredArgs=[]\n", otherFile)
	helperPrint ("\t\toptionalArgs=['data', 'connection']\n", otherFile)
	helperPrint ("\t\tar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())\n", otherFile)
	helperPrint ("\t\tdata=ar['data']\n", otherFile)
	helperPrint ("\t\tself.data=ar['data']\n", otherFile)
	helperPrint ("\t\tself.connection=ar['connection']\n", otherFile)
	for var in swFieldList:
		func = lambda s: s[:1].lower() + s[1:] if s else ''
		var = var.replace(',','')
		var1 = func(var)
		helperPrint ("\t\ttry:\n", otherFile)
		helperPrint ("\t\t\tself.%s=data['%s']\n"%(var1,var), otherFile)
		helperPrint ("\t\texcept:\n", otherFile)
		helperPrint ("\t\t\tself.%s=None\n"%(var1), otherFile)
	helperPrint('\n', otherFile)
	cStat="\tdef create(self,connection):\n\t\tswFieldList={"
	for var in swFieldList:
		func = lambda s: s[:1].lower() + s[1:] if s else ''
		var = var.replace(',','')
		var1 = func(var)
		helperPrint ("\tdef get%s(self):\n\t\treturn self.%s\n"%(var,var1), otherFile)




