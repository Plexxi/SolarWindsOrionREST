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
import urllib2,base64,httplib,json,sys,urllib,inspect,traceback,md5
from time import *
from swCommonLib import *

# Set DEBUG either 1 or 2 for extensive logging info
global DEBUG
DEBUG = 0

#
# Main SolarWinds class. 
# Instantiate an object of this class, with valid credentials as arguments
# and call appropriate 'get' method to retrieve data from SolarWinds db
#

class SolarWinds():
	def __init__(self,**kwargs):
		requiredArgs=["ip"]
		optionalArgs=["username", "password", "auth_key", "port"]
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		if not ar:
			print '####### Bad args, no IP set'
		self.ip=ar['ip']
		self.username=ar['username']
		self.password=ar['password']
		self.auth_key=ar['auth_key']
		if ar['port']:
			self.port=ar['port']
		else:
			self.port=17778

		# special checking need to see either username or auth_key, blank password is valid
		if not ar['username'] and not ar['auth_key']  :
			print '####### Bad args, no username/password or auth_key'

		self.connection=None
		self.header = self.createHeader()

        
	def connect(self):
		#Create connection
		return self.https()


	def https(self):
		if DEBUG:
			httplib.HTTPSConnection.debuglevel = 1
		return httplib.HTTPSConnection(self.ip,self.port)

        def createHeader(self):
		#Set the correct html header which could be device specific
		header = {'Accept':'application/json',"Content-Type":"application/json"}
		#Use the auth_key if its there, else encode the username/password
		if not self.auth_key:
			self.auth_key = base64.encodestring('%s:%s'%(self.username,self.password))
		#Create the final header
		header['authorization'] = 'Basic %s' % self.auth_key
		if DEBUG:
			print header
		return header

	def sendRequest(self,**kwargs):
		requiredArgs=["Type","URL","status"]
		optionalArgs=["payload"]
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		payload=ar['payload']
		Type=ar['Type']
		URL=ar['URL']
		status=ar['status']

		conn = self.connect()
		caller = inspect.stack()

	#This allows us to dump the calling function in case of errors

		if payload:
			payload = json.dumps(payload, ensure_ascii=False)
			payload.encode('utf-8')

			debugPrint("")
        #Attempt to connect using the given details.
        #If the connection fails, return False and dump the calling function

		debugPrint("In sendRequest")
		debugPrint("Type = %s"%(Type))
		debugPrint("URL = %s"%(URL))
		debugPrint("payload = %s"%(payload))
		debugPrint("header = %s"%(self.header))
		try:
			conn.request(Type,URL,payload,self.header)
		except:
			print "Could not connect in call from %s. Unable to continue"%(caller)
			return None
        #If we are here, the connection was successful, now we need to ensure that we got a
        #response that we were expecting.
		response = conn.getresponse()
		if DEBUG:
			debugPrint("#################\nResponse header = %s\n#################"%(response.getheaders()))
			if status == 0:
				print "Expected Status is 0 - ignoring. Actual = %s"%(response.status)
			else:
				print "Response Status from %s = %s. Expecting %s"%(caller,response.status,status)
        #status is passed into the call and is the http response status expeted from the call.
        #If the passed in status is 0, ifgnore this check
		if status:
                        #if we dont get the response we expected, we must stop
			if response.status != status:
				print "Received HTTP response %s from %s. Caller is %s. Unable to continue"%(response.status,self.ip,caller)
				return None
        #Not all data can be passed back as a json.loads format. Try to pass it back in this format
        #but if it fails, just pass it back unformatted.
		try:
			data = json.loads(response.read())
		except:
			data = response.read()
        #return the data
		return data


	def getOrionAccounts(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionAccountsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['AccountID', 'Enabled', 'AllowNodeManagement', 'AllowAdmin', 'CanClearEvents', 'AllowReportManagement', 'Expires', 'LastLogin', 'LimitationID1', 'LimitationID2', 'LimitationID3', 'AccountSID', 'AccountType']
		tableName = 'Orion.Accounts'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionAccounts = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionAccounts == None:
				return []
		for obj in currOrionAccounts['results']:
			thisObj = OrionAccounts(connection=self,data=obj)
			self.orionAccountsObjs.append(thisObj)
		return self.orionAccountsObjs

	def getOrionActiveAlerts(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionActiveAlertsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['AlertID', 'AlertTime', 'ObjectType', 'ObjectID', 'ObjectName', 'NodeID', 'NodeName', 'EventMessage', 'propertyID', 'Monitoredproperty', 'CurrentValue', 'TriggerValue', 'ResetValue', 'EngineID', 'AlertNotes', 'ExpireTime']
		tableName = 'Orion.ActiveAlerts'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionActiveAlerts = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionActiveAlerts == None:
				return []
		for obj in currOrionActiveAlerts['results']:
			thisObj = OrionActiveAlerts(connection=self,data=obj)
			self.orionActiveAlertsObjs.append(thisObj)
		return self.orionActiveAlertsObjs

	def getOrionAlertDefinitions(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionAlertDefinitionsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['AlertDefID', 'Name', 'Description', 'Enabled', 'StartTime', 'EndTime', 'DOW', 'TriggerQuery', 'TriggerQueryDesign', 'ResetQuery', 'ResetQueryDesign', 'SuppressionQuery', 'SuppressionQueryDesign', 'TriggerSustained', 'ResetSustained', 'LastExecuteTime', 'ExecuteInterval', 'BlockUntil', 'ResponseTime', 'LastErrorTime', 'LastError', 'ObjectType']
		tableName = 'Orion.AlertDefinitions'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionAlertDefinitions = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionAlertDefinitions == None:
				return []
		for obj in currOrionAlertDefinitions['results']:
			thisObj = OrionAlertDefinitions(connection=self,data=obj)
			self.orionAlertDefinitionsObjs.append(thisObj)
		return self.orionAlertDefinitionsObjs

	def getOrionAlerts(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionAlertsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['EngineID', 'AlertID', 'Name', 'Enabled', 'Description', 'StartTime', 'EndTime', 'DOW', 'NetObjects', 'propertyID', 'Trigger', 'Reset', 'Sustained', 'TriggerSubjectTemplate', 'TriggerMessageTemplate', 'ResetSubjectTemplate', 'ResetMessageTemplate', 'Frequency', 'EMailAddresses', 'ReplyName', 'ReplyAddress', 'LogFile', 'LogMessage', 'ShellTrigger', 'ShellReset', 'SuppressionType', 'Suppression']
		tableName = 'Orion.Alerts'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionAlerts = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionAlerts == None:
				return []
		for obj in currOrionAlerts['results']:
			thisObj = OrionAlerts(connection=self,data=obj)
			self.orionAlertsObjs.append(thisObj)
		return self.orionAlertsObjs

	def getOrionAlertStatus(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionAlertStatusObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['AlertDefID', 'ActiveObject', 'ObjectType', 'State', 'WorkingState', 'ObjectName', 'AlertMessage', 'TriggerTimeStamp', 'TriggerTimeOffset', 'TriggerCount', 'ResetTimeStamp', 'Acknowledged', 'AcknowledgedBy', 'AcknowledgedTime', 'LastUpdate', 'AlertNotes', 'Notes']
		tableName = 'Orion.AlertStatus'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionAlertStatus = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionAlertStatus == None:
				return []
		for obj in currOrionAlertStatus['results']:
			thisObj = OrionAlertStatus(connection=self,data=obj)
			self.orionAlertStatusObjs.append(thisObj)
		return self.orionAlertStatusObjs

	def getOrionAuditingActionTypes(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionAuditingActionTypesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['ActionTypeID', 'ActionType', 'ActionTypeDisplayName']
		tableName = 'Orion.AuditingActionTypes'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionAuditingActionTypes = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionAuditingActionTypes == None:
				return []
		for obj in currOrionAuditingActionTypes['results']:
			thisObj = OrionAuditingActionTypes(connection=self,data=obj)
			self.orionAuditingActionTypesObjs.append(thisObj)
		return self.orionAuditingActionTypesObjs

	def getOrionAuditingArguments(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionAuditingArgumentsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['AuditEventID', 'ArgsKey', 'ArgsValue']
		tableName = 'Orion.AuditingArguments'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionAuditingArguments = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionAuditingArguments == None:
				return []
		for obj in currOrionAuditingArguments['results']:
			thisObj = OrionAuditingArguments(connection=self,data=obj)
			self.orionAuditingArgumentsObjs.append(thisObj)
		return self.orionAuditingArgumentsObjs

	def getOrionAuditingEvents(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionAuditingEventsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['AuditEventID', 'TimeLoggedUtc', 'AccountID', 'ActionTypeID', 'AuditEventMessage', 'NetworkNode', 'NetObjectID', 'NetObjectType']
		tableName = 'Orion.AuditingEvents'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionAuditingEvents = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionAuditingEvents == None:
				return []
		for obj in currOrionAuditingEvents['results']:
			thisObj = OrionAuditingEvents(connection=self,data=obj)
			self.orionAuditingEventsObjs.append(thisObj)
		return self.orionAuditingEventsObjs

	def getOrionContainer(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionContainerObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['ContainerID', 'Name', 'Owner', 'Frequency', 'StatusCalculator', 'RollupType', 'IsDeleted', 'PollingEnabled', 'LastChanged']
		tableName = 'Orion.Container'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionContainer = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionContainer == None:
				return []
		for obj in currOrionContainer['results']:
			thisObj = OrionContainer(connection=self,data=obj)
			self.orionContainerObjs.append(thisObj)
		return self.orionContainerObjs

	def getOrionContainerMemberDefinition(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionContainerMemberDefinitionObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['DefinitionID', 'ContainerID', 'Name', 'Entity', 'FromClause', 'Expression', 'Definition']
		tableName = 'Orion.ContainerMemberDefinition'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionContainerMemberDefinition = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionContainerMemberDefinition == None:
				return []
		for obj in currOrionContainerMemberDefinition['results']:
			thisObj = OrionContainerMemberDefinition(connection=self,data=obj)
			self.orionContainerMemberDefinitionObjs.append(thisObj)
		return self.orionContainerMemberDefinitionObjs

	def getOrionContainerMembers(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionContainerMembersObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['ContainerID', 'MemberPrimaryID', 'MemberEntityType', 'Name', 'Status', 'MemberUri', 'MemberAncestorDisplayNames', 'MemberAncestorDetailsUrls']
		tableName = 'Orion.ContainerMembers'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionContainerMembers = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionContainerMembers == None:
				return []
		for obj in currOrionContainerMembers['results']:
			thisObj = OrionContainerMembers(connection=self,data=obj)
			self.orionContainerMembersObjs.append(thisObj)
		return self.orionContainerMembersObjs

	def getOrionContainerMemberSnapshots(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionContainerMemberSnapshotsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['ContainerMemberSnapshotID', 'ContainerID', 'Name', 'FullName', 'EntityDisplayName', 'EntityDisplayNamePlural', 'MemberUri', 'Status']
		tableName = 'Orion.ContainerMemberSnapshots'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionContainerMemberSnapshots = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionContainerMemberSnapshots == None:
				return []
		for obj in currOrionContainerMemberSnapshots['results']:
			thisObj = OrionContainerMemberSnapshots(connection=self,data=obj)
			self.orionContainerMemberSnapshotsObjs.append(thisObj)
		return self.orionContainerMemberSnapshotsObjs

	def getOrionCPUMultiLoad(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionCPUMultiLoadObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['NodeID', 'TimeStampUTC', 'CPUIndex', 'MinLoad', 'MaxLoad', 'AvgLoad']
		tableName = 'Orion.CPUMultiLoad'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionCPUMultiLoad = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionCPUMultiLoad == None:
				return []
		for obj in currOrionCPUMultiLoad['results']:
			thisObj = OrionCPUMultiLoad(connection=self,data=obj)
			self.orionCPUMultiLoadObjs.append(thisObj)
		return self.orionCPUMultiLoadObjs

	def getOrionCredential(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionCredentialObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['ID', 'Name', 'Description', 'CredentialType', 'CredentialOwner']
		tableName = 'Orion.Credential'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionCredential = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionCredential == None:
				return []
		for obj in currOrionCredential['results']:
			thisObj = OrionCredential(connection=self,data=obj)
			self.orionCredentialObjs.append(thisObj)
		return self.orionCredentialObjs

	def getOrionCustomProperty(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionCustomPropertyObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['Table', 'Field', 'DataType', 'MaxLength', 'StorageMethod', 'Description', 'TargetEntity']
		tableName = 'Orion.CustomProperty'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionCustomProperty = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionCustomProperty == None:
				return []
		for obj in currOrionCustomProperty['results']:
			thisObj = OrionCustomProperty(connection=self,data=obj)
			self.orionCustomPropertyObjs.append(thisObj)
		return self.orionCustomPropertyObjs

	def getOrionCustomPropertyUsage(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionCustomPropertyUsageObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['Table', 'Field', 'IsForAlerting', 'IsForFiltering', 'IsForGrouping', 'IsForReporting', 'IsForEntityDetail']
		tableName = 'Orion.CustomPropertyUsage'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionCustomPropertyUsage = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionCustomPropertyUsage == None:
				return []
		for obj in currOrionCustomPropertyUsage['results']:
			thisObj = OrionCustomPropertyUsage(connection=self,data=obj)
			self.orionCustomPropertyUsageObjs.append(thisObj)
		return self.orionCustomPropertyUsageObjs

	def getOrionCustomPropertyValues(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionCustomPropertyValuesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['Table', 'Field', 'Value']
		tableName = 'Orion.CustomPropertyValues'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionCustomPropertyValues = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionCustomPropertyValues == None:
				return []
		for obj in currOrionCustomPropertyValues['results']:
			thisObj = OrionCustomPropertyValues(connection=self,data=obj)
			self.orionCustomPropertyValuesObjs.append(thisObj)
		return self.orionCustomPropertyValuesObjs

	def getOrionDependencies(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionDependenciesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['DependencyId', 'Name', 'ParentUri', 'ChildUri', 'LastUpdateUTC']
		tableName = 'Orion.Dependencies'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionDependencies = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionDependencies == None:
				return []
		for obj in currOrionDependencies['results']:
			thisObj = OrionDependencies(connection=self,data=obj)
			self.orionDependenciesObjs.append(thisObj)
		return self.orionDependenciesObjs

	def getOrionDependencyEntities(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionDependencyEntitiesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['EntityName', 'ValidParent', 'ValidChild']
		tableName = 'Orion.DependencyEntities'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionDependencyEntities = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionDependencyEntities == None:
				return []
		for obj in currOrionDependencyEntities['results']:
			thisObj = OrionDependencyEntities(connection=self,data=obj)
			self.orionDependencyEntitiesObjs.append(thisObj)
		return self.orionDependencyEntitiesObjs

	def getOrionDiscoveredNodes(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionDiscoveredNodesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['NodeID', 'ProfileID', 'IPAddress', 'IPAddressGUID', 'SnmpVersion', 'SubType', 'CredentialID', 'Hostname', 'DNS', 'SysObjectID', 'Vendor', 'VendorIcon', 'MachineType', 'SysDescription', 'SysName', 'Location', 'Contact', 'IgnoredNodeID']
		tableName = 'Orion.DiscoveredNodes'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionDiscoveredNodes = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionDiscoveredNodes == None:
				return []
		for obj in currOrionDiscoveredNodes['results']:
			thisObj = OrionDiscoveredNodes(connection=self,data=obj)
			self.orionDiscoveredNodesObjs.append(thisObj)
		return self.orionDiscoveredNodesObjs

	def getOrionDiscoveredPollers(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionDiscoveredPollersObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['ID', 'ProfileID', 'NetObjectID', 'NetObjectType', 'PollerType']
		tableName = 'Orion.DiscoveredPollers'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionDiscoveredPollers = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionDiscoveredPollers == None:
				return []
		for obj in currOrionDiscoveredPollers['results']:
			thisObj = OrionDiscoveredPollers(connection=self,data=obj)
			self.orionDiscoveredPollersObjs.append(thisObj)
		return self.orionDiscoveredPollersObjs

	def getOrionDiscoveredVolumes(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionDiscoveredVolumesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['ProfileID', 'DiscoveredNodeID', 'VolumeIndex', 'VolumeType', 'VolumeDescription', 'IgnoredVolumeID']
		tableName = 'Orion.DiscoveredVolumes'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionDiscoveredVolumes = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionDiscoveredVolumes == None:
				return []
		for obj in currOrionDiscoveredVolumes['results']:
			thisObj = OrionDiscoveredVolumes(connection=self,data=obj)
			self.orionDiscoveredVolumesObjs.append(thisObj)
		return self.orionDiscoveredVolumesObjs

	def getOrionDiscoveryProfiles(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionDiscoveryProfilesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['ProfileID', 'Name', 'Description', 'RunTimeInSeconds', 'LastRun', 'EngineID', 'Status', 'JobID', 'SIPPort', 'HopCount', 'SearchTimeout', 'SNMPTimeout', 'SNMPRetries', 'RepeatInterval', 'Active', 'DuplicateNodes', 'ImportUpInterface', 'ImportDownInterface', 'ImportShutdownInterface', 'SelectionMethod', 'JobTimeout', 'ScheduleRunAtTime', 'ScheduleRunFrequency', 'StatusDescription', 'IsHidden', 'IsAutoImport']
		tableName = 'Orion.DiscoveryProfiles'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionDiscoveryProfiles = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionDiscoveryProfiles == None:
				return []
		for obj in currOrionDiscoveryProfiles['results']:
			thisObj = OrionDiscoveryProfiles(connection=self,data=obj)
			self.orionDiscoveryProfilesObjs.append(thisObj)
		return self.orionDiscoveryProfilesObjs

	def getOrionElementInfo(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionElementInfoObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['ElementType', 'MaxElementCount']
		tableName = 'Orion.ElementInfo'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionElementInfo = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionElementInfo == None:
				return []
		for obj in currOrionElementInfo['results']:
			thisObj = OrionElementInfo(connection=self,data=obj)
			self.orionElementInfoObjs.append(thisObj)
		return self.orionElementInfoObjs

	def getOrionEvents(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionEventsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['EventID', 'EventTime', 'NetworkNode', 'NetObjectID', 'EventType', 'Message', 'Acknowledged', 'NetObjectType', 'TimeStamp']
		tableName = 'Orion.Events'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionEvents = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionEvents == None:
				return []
		for obj in currOrionEvents['results']:
			thisObj = OrionEvents(connection=self,data=obj)
			self.orionEventsObjs.append(thisObj)
		return self.orionEventsObjs

	def getOrionEventTypes(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionEventTypesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['EventType', 'Name', 'Bold', 'BackColor', 'Icon', 'Sort', 'Notify', 'Record', 'Sound', 'Mute', 'NotifyMessage', 'NotifySubject']
		tableName = 'Orion.EventTypes'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionEventTypes = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionEventTypes == None:
				return []
		for obj in currOrionEventTypes['results']:
			thisObj = OrionEventTypes(connection=self,data=obj)
			self.orionEventTypesObjs.append(thisObj)
		return self.orionEventTypesObjs

	def getOrionNodeIPAddresses(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionNodeIPAddressesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['NodeID', 'IPAddress', 'IPAddressN', 'IPAddressType', 'InterfaceIndex']
		tableName = 'Orion.NodeIPAddresses'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionNodeIPAddresses = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionNodeIPAddresses == None:
				return []
		for obj in currOrionNodeIPAddresses['results']:
			thisObj = OrionNodeIPAddresses(connection=self,data=obj)
			self.orionNodeIPAddressesObjs.append(thisObj)
		return self.orionNodeIPAddressesObjs

	def getOrionNodeL2Connections(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionNodeL2ConnectionsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['NodeID', 'PortID', 'MACAddress', 'Status', 'VlanId']
		tableName = 'Orion.NodeL2Connections'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionNodeL2Connections = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionNodeL2Connections == None:
				return []
		for obj in currOrionNodeL2Connections['results']:
			thisObj = OrionNodeL2Connections(connection=self,data=obj)
			self.orionNodeL2ConnectionsObjs.append(thisObj)
		return self.orionNodeL2ConnectionsObjs

	def getOrionNodeL3Entries(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionNodeL3EntriesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['NodeID', 'IfIndex', 'MACAddress', 'IPAddress', 'Type']
		tableName = 'Orion.NodeL3Entries'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionNodeL3Entries = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionNodeL3Entries == None:
				return []
		for obj in currOrionNodeL3Entries['results']:
			thisObj = OrionNodeL3Entries(connection=self,data=obj)
			self.orionNodeL3EntriesObjs.append(thisObj)
		return self.orionNodeL3EntriesObjs

	def getOrionNodeLldpEntry(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionNodeLldpEntryObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['NodeID', 'LocalPortNumber', 'RemoteIfIndex', 'RemotePortId', 'RemotePortDescription', 'RemoteSystemName', 'RemoteIpAddress']
		tableName = 'Orion.NodeLldpEntry'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionNodeLldpEntry = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionNodeLldpEntry == None:
				return []
		for obj in currOrionNodeLldpEntry['results']:
			thisObj = OrionNodeLldpEntry(connection=self,data=obj)
			self.orionNodeLldpEntryObjs.append(thisObj)
		return self.orionNodeLldpEntryObjs

	def getOrionNodeMACAddresses(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionNodeMACAddressesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['NodeID', 'MAC', 'DateTime']
		tableName = 'Orion.NodeMACAddresses'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionNodeMACAddresses = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionNodeMACAddresses == None:
				return []
		for obj in currOrionNodeMACAddresses['results']:
			thisObj = OrionNodeMACAddresses(connection=self,data=obj)
			self.orionNodeMACAddressesObjs.append(thisObj)
		return self.orionNodeMACAddressesObjs

	def getOrionNodes(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionNodesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['NodeID', 'ObjectSubType', 'IPAddress', 'IPAddressType', 'DynamicIP', 'Caption', 'NodeDescription', 'DNS', 'SysName', 'Vendor', 'SysObjectID', 'Location', 'Contact', 'VendorIcon', 'Icon', 'IOSImage', 'IOSVersion', 'GroupStatus', 'StatusIcon', 'LastBoot', 'SystemUpTime', 'ResponseTime', 'PercentLoss', 'AvgResponseTime', 'MinResponseTime', 'MaxResponseTime', 'CPULoad', 'MemoryUsed', 'PercentMemoryUsed', 'LastSync', 'LastSystemUpTimePollUtc', 'MachineType', 'Severity', 'ChildStatus', 'Allow64BitCounters', 'AgentPort', 'TotalMemory', 'CMTS', 'CustomPollerLastStatisticsPoll', 'CustomPollerLastStatisticsPollSuccess', 'SNMPVersion', 'PollInterval', 'EngineID', 'RediscoveryInterval', 'NextPoll', 'NextRediscovery', 'StatCollection', 'External', 'Community', 'RWCommunity', 'IP', 'IP_Address', 'IPAddressGUID', 'NodeName', 'BlockUntil', 'BufferNoMemThisHour', 'BufferNoMemToday', 'BufferSmMissThisHour', 'BufferSmMissToday', 'BufferMdMissThisHour', 'BufferMdMissToday', 'BufferBgMissThisHour', 'BufferBgMissToday', 'BufferLgMissThisHour', 'BufferLgMissToday', 'BufferHgMissThisHour', 'BufferHgMissToday', 'OrionIdPrefix', 'OrionIdColumn']
		tableName = 'Orion.Nodes'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionNodes = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionNodes == None:
				return []
		for obj in currOrionNodes['results']:
			thisObj = OrionNodes(connection=self,data=obj)
			self.orionNodesObjs.append(thisObj)
		return self.orionNodesObjs

	def getOrionNodesCustomProperties(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionNodesCustomPropertiesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['NodeID', 'City', 'Comments', 'Department']
		tableName = 'Orion.NodesCustomProperties'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionNodesCustomProperties = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionNodesCustomProperties == None:
				return []
		for obj in currOrionNodesCustomProperties['results']:
			thisObj = OrionNodesCustomProperties(connection=self,data=obj)
			self.orionNodesCustomPropertiesObjs.append(thisObj)
		return self.orionNodesCustomPropertiesObjs

	def getOrionNodesStats(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionNodesStatsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['AvgResponseTime', 'MinResponseTime', 'MaxResponseTime', 'ResponseTime', 'PercentLoss', 'CPULoad', 'MemoryUsed', 'PercentMemoryUsed', 'LastBoot', 'SystemUpTime', 'NodeID']
		tableName = 'Orion.NodesStats'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionNodesStats = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionNodesStats == None:
				return []
		for obj in currOrionNodesStats['results']:
			thisObj = OrionNodesStats(connection=self,data=obj)
			self.orionNodesStatsObjs.append(thisObj)
		return self.orionNodesStatsObjs

	def getOrionNodeVlans(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionNodeVlansObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['NodeID', 'VlanId']
		tableName = 'Orion.NodeVlans'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionNodeVlans = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionNodeVlans == None:
				return []
		for obj in currOrionNodeVlans['results']:
			thisObj = OrionNodeVlans(connection=self,data=obj)
			self.orionNodeVlansObjs.append(thisObj)
		return self.orionNodeVlansObjs

	def getOrionNPMDiscoveredInterfaces(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionNPMDiscoveredInterfacesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['ProfileID', 'DiscoveredNodeID', 'DiscoveredInterfaceID', 'InterfaceIndex', 'InterfaceName', 'InterfaceType', 'InterfaceSubType', 'InterfaceTypeDescription', 'OperStatus', 'AdminStatus', 'PhysicalAddress', 'IfName', 'InterfaceAlias', 'InterfaceTypeName', 'IgnoredInterfaceID']
		tableName = 'Orion.NPM.DiscoveredInterfaces'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionNPMDiscoveredInterfaces = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionNPMDiscoveredInterfaces == None:
				return []
		for obj in currOrionNPMDiscoveredInterfaces['results']:
			thisObj = OrionNPMDiscoveredInterfaces(connection=self,data=obj)
			self.orionNPMDiscoveredInterfacesObjs.append(thisObj)
		return self.orionNPMDiscoveredInterfacesObjs

	def getOrionNPMInterfaceAvailability(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionNPMInterfaceAvailabilityObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['DateTime', 'InterfaceID', 'NodeID', 'Availability', 'Weight']
		tableName = 'Orion.NPM.InterfaceAvailability'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionNPMInterfaceAvailability = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionNPMInterfaceAvailability == None:
				return []
		for obj in currOrionNPMInterfaceAvailability['results']:
			thisObj = OrionNPMInterfaceAvailability(connection=self,data=obj)
			self.orionNPMInterfaceAvailabilityObjs.append(thisObj)
		return self.orionNPMInterfaceAvailabilityObjs

	def getOrionNPMInterfaceErrors(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionNPMInterfaceErrorsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['NodeID', 'InterfaceID', 'DateTime', 'Archive', 'InErrors', 'InDiscards', 'OutErrors', 'OutDiscards']
		tableName = 'Orion.NPM.InterfaceErrors'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionNPMInterfaceErrors = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionNPMInterfaceErrors == None:
				return []
		for obj in currOrionNPMInterfaceErrors['results']:
			thisObj = OrionNPMInterfaceErrors(connection=self,data=obj)
			self.orionNPMInterfaceErrorsObjs.append(thisObj)
		return self.orionNPMInterfaceErrorsObjs

	def getOrionNPMInterfaces(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionNPMInterfacesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['NodeID', 'InterfaceID', 'ObjectSubType', 'Name', 'Index', 'Icon', 'Type', 'TypeName', 'TypeDescription', 'Speed', 'MTU', 'LastChange', 'PhysicalAddress', 'AdminStatus', 'OperStatus', 'StatusIcon', 'InBandwidth', 'OutBandwidth', 'Caption', 'FullName', 'Outbps', 'Inbps', 'OutPercentUtil', 'InPercentUtil', 'OutPps', 'InPps', 'InPktSize', 'OutPktSize', 'OutUcastPps', 'OutMcastPps', 'InUcastPps', 'InMcastPps', 'InDiscardsThisHour', 'InDiscardsToday', 'InErrorsThisHour', 'InErrorsToday', 'OutDiscardsThisHour', 'OutDiscardsToday', 'OutErrorsThisHour', 'OutErrorsToday', 'MaxInBpsToday', 'MaxInBpsTime', 'MaxOutBpsToday', 'MaxOutBpsTime', 'Counter64', 'LastSync', 'Alias', 'IfName', 'Severity', 'CustomBandwidth', 'CustomPollerLastStatisticsPoll', 'PollInterval', 'NextPoll', 'RediscoveryInterval', 'NextRediscovery', 'StatCollection', 'UnPluggable', 'InterfaceSpeed', 'InterfaceCaption', 'InterfaceType', 'InterfaceSubType', 'MAC', 'InterfaceName', 'InterfaceIcon', 'InterfaceTypeName', 'AdminStatusLED', 'OperStatusLED', 'InterfaceAlias', 'InterfaceIndex', 'InterfaceLastChange', 'InterfaceMTU', 'InterfaceTypeDescription', 'OrionIdPrefix', 'OrionIdColumn']
		tableName = 'Orion.NPM.Interfaces'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionNPMInterfaces = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionNPMInterfaces == None:
				return []
		for obj in currOrionNPMInterfaces['results']:
			thisObj = OrionNPMInterfaces(connection=self,data=obj)
			self.orionNPMInterfacesObjs.append(thisObj)
		return self.orionNPMInterfacesObjs

	def getOrionNPMInterfaceTraffic(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionNPMInterfaceTrafficObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['NodeID', 'InterfaceID', 'DateTime', 'Archive', 'InAveragebps', 'InMinbps', 'InMaxbps', 'InTotalBytes', 'InTotalPkts', 'InAvgUniCastPkts', 'InMinUniCastPkts', 'InMaxUniCastPkts', 'InAvgMultiCastPkts', 'InMinMultiCastPkts', 'InMaxMultiCastPkts', 'OutAveragebps', 'OutMinbps', 'OutMaxbps', 'OutTotalBytes', 'OutTotalPkts', 'OutAvgUniCastPkts', 'OutMaxUniCastPkts', 'OutMinUniCastPkts', 'OutAvgMultiCastPkts', 'OutMinMultiCastPkts', 'OutMaxMultiCastPkts']
		tableName = 'Orion.NPM.InterfaceTraffic'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionNPMInterfaceTraffic = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionNPMInterfaceTraffic == None:
				return []
		for obj in currOrionNPMInterfaceTraffic['results']:
			thisObj = OrionNPMInterfaceTraffic(connection=self,data=obj)
			self.orionNPMInterfaceTrafficObjs.append(thisObj)
		return self.orionNPMInterfaceTrafficObjs

	def getOrionPollers(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionPollersObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['PollerID', 'PollerType', 'NetObject', 'NetObjectType', 'NetObjectID', 'Enabled']
		tableName = 'Orion.Pollers'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionPollers = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionPollers == None:
				return []
		for obj in currOrionPollers['results']:
			thisObj = OrionPollers(connection=self,data=obj)
			self.orionPollersObjs.append(thisObj)
		return self.orionPollersObjs

	def getOrionReport(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionReportObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['ReportID', 'Name', 'Category', 'Title', 'Type', 'SubTitle', 'Description', 'LegacyPath', 'Definition', 'ModuleTitle', 'RecipientList', 'LimitationCategory', 'Owner', 'LastRenderDuration']
		tableName = 'Orion.Report'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionReport = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionReport == None:
				return []
		for obj in currOrionReport['results']:
			thisObj = OrionReport(connection=self,data=obj)
			self.orionReportObjs.append(thisObj)
		return self.orionReportObjs

	def getOrionResponseTime(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionResponseTimeObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['NodeID', 'DateTime', 'Archive', 'AvgResponseTime', 'MinResponseTime', 'MaxResponseTime', 'PercentLoss', 'Availability']
		tableName = 'Orion.ResponseTime'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionResponseTime = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionResponseTime == None:
				return []
		for obj in currOrionResponseTime['results']:
			thisObj = OrionResponseTime(connection=self,data=obj)
			self.orionResponseTimeObjs.append(thisObj)
		return self.orionResponseTimeObjs

	def getOrionServices(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionServicesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['DisplayName', 'ServiceName', 'Status', 'Memory']
		tableName = 'Orion.Services'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionServices = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionServices == None:
				return []
		for obj in currOrionServices['results']:
			thisObj = OrionServices(connection=self,data=obj)
			self.orionServicesObjs.append(thisObj)
		return self.orionServicesObjs

	def getOrionSysLog(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionSysLogObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['MessageID', 'EngineID', 'DateTime', 'IPAddress', 'Acknowledged', 'SysLogFacility', 'SysLogSeverity', 'Hostname', 'MessageType', 'Message', 'SysLogTag', 'FirstIPInMessage', 'SecIPInMessage', 'MacInMessage', 'TimeStamp', 'NodeID']
		tableName = 'Orion.SysLog'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionSysLog = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionSysLog == None:
				return []
		for obj in currOrionSysLog['results']:
			thisObj = OrionSysLog(connection=self,data=obj)
			self.orionSysLogObjs.append(thisObj)
		return self.orionSysLogObjs

	def getOrionTopologyData(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionTopologyDataObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['DiscoveryProfileID', 'SrcNodeID', 'SrcInterfaceID', 'DestNodeID', 'DestInterfaceID', 'SrcType', 'DestType', 'DataSourceNodeID', 'LastUpdateUtc']
		tableName = 'Orion.TopologyData'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionTopologyData = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionTopologyData == None:
				return []
		for obj in currOrionTopologyData['results']:
			thisObj = OrionTopologyData(connection=self,data=obj)
			self.orionTopologyDataObjs.append(thisObj)
		return self.orionTopologyDataObjs

	def getOrionTraps(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionTrapsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['TrapID', 'EngineID', 'DateTime', 'IPAddress', 'Community', 'Tag', 'Acknowledged', 'Hostname', 'NodeID', 'TrapType', 'ColorCode', 'TimeStamp']
		tableName = 'Orion.Traps'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionTraps = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionTraps == None:
				return []
		for obj in currOrionTraps['results']:
			thisObj = OrionTraps(connection=self,data=obj)
			self.orionTrapsObjs.append(thisObj)
		return self.orionTrapsObjs

	def getOrionViews(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionViewsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['ViewID', 'ViewKey', 'ViewTitle', 'ViewType', 'Columns', 'Column1Width', 'Column2Width', 'Column3Width', 'System', 'Customizable', 'LimitationID']
		tableName = 'Orion.Views'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionViews = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionViews == None:
				return []
		for obj in currOrionViews['results']:
			thisObj = OrionViews(connection=self,data=obj)
			self.orionViewsObjs.append(thisObj)
		return self.orionViewsObjs

	def getOrionVIMClusters(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionVIMClustersObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['ClusterID', 'ManagedObjectID', 'DataCenterID', 'Name', 'TotalMemory', 'TotalCpu', 'CpuCoreCount', 'CpuThreadCount', 'EffectiveCpu', 'EffectiveMemory', 'DrsBehaviour', 'DrsStatus', 'DrsVmotionRate', 'HaAdmissionControlStatus', 'HaStatus', 'HaFailoverLevel', 'ConfigStatus', 'OverallStatus', 'CPULoad', 'CPUUsageMHz', 'MemoryUsage', 'MemoryUsageMB']
		tableName = 'Orion.VIM.Clusters'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionVIMClusters = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionVIMClusters == None:
				return []
		for obj in currOrionVIMClusters['results']:
			thisObj = OrionVIMClusters(connection=self,data=obj)
			self.orionVIMClustersObjs.append(thisObj)
		return self.orionVIMClustersObjs

	def getOrionVIMClusterStatistics(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionVIMClusterStatisticsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['ClusterID', 'DateTime', 'PercentAvailability', 'MinCPULoad', 'MaxCPULoad', 'AvgCPULoad', 'MinCPUUsageMHz', 'MaxCPUUsageMHz', 'AvgCPUUsageMHz', 'MinMemoryUsage', 'MaxMemoryUsage', 'AvgMemoryUsage', 'MinMemoryUsageMB', 'MaxMemoryUsageMB', 'AvgMemoryUsageMB']
		tableName = 'Orion.VIM.ClusterStatistics'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionVIMClusterStatistics = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionVIMClusterStatistics == None:
				return []
		for obj in currOrionVIMClusterStatistics['results']:
			thisObj = OrionVIMClusterStatistics(connection=self,data=obj)
			self.orionVIMClusterStatisticsObjs.append(thisObj)
		return self.orionVIMClusterStatisticsObjs

	def getOrionVIMDataCenters(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionVIMDataCentersObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['DataCenterID', 'ManagedObjectID', 'VCenterID', 'Name', 'ConfigStatus', 'OverallStatus', 'ManagedStatus']
		tableName = 'Orion.VIM.DataCenters'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionVIMDataCenters = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionVIMDataCenters == None:
				return []
		for obj in currOrionVIMDataCenters['results']:
			thisObj = OrionVIMDataCenters(connection=self,data=obj)
			self.orionVIMDataCentersObjs.append(thisObj)
		return self.orionVIMDataCentersObjs

	def getOrionVIMHostIPAddresses(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionVIMHostIPAddressesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['HostID', 'IPAddress']
		tableName = 'Orion.VIM.HostIPAddresses'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionVIMHostIPAddresses = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionVIMHostIPAddresses == None:
				return []
		for obj in currOrionVIMHostIPAddresses['results']:
			thisObj = OrionVIMHostIPAddresses(connection=self,data=obj)
			self.orionVIMHostIPAddressesObjs.append(thisObj)
		return self.orionVIMHostIPAddressesObjs

	def getOrionVIMHosts(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionVIMHostsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['HostID', 'ManagedObjectID', 'NodeID', 'HostName', 'ClusterID', 'DataCenterID', 'VMwareProductName', 'VMwareProductVersion', 'PollingJobID', 'ServiceURIID', 'CredentialID', 'HostStatus', 'PollingMethod', 'Model', 'Vendor', 'ProcessorType', 'CpuCoreCount', 'CpuPkgCount', 'CpuMhz', 'NicCount', 'HbaCount', 'HbaFcCount', 'HbaScsiCount', 'HbaIscsiCount', 'MemorySize', 'BuildNumber', 'BiosSerial', 'IPAddress', 'ConnectionState', 'ConfigStatus', 'OverallStatus', 'NodeStatus', 'NetworkUtilization', 'NetworkUsageRate', 'NetworkTransmitRate', 'NetworkReceiveRate', 'NetworkCapacityKbps', 'CpuLoad', 'CpuUsageMHz', 'MemUsage', 'MemUsageMB', 'VmCount', 'VmRunningCount', 'StatusMessage', 'PlatformID']
		tableName = 'Orion.VIM.Hosts'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionVIMHosts = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionVIMHosts == None:
				return []
		for obj in currOrionVIMHosts['results']:
			thisObj = OrionVIMHosts(connection=self,data=obj)
			self.orionVIMHostsObjs.append(thisObj)
		return self.orionVIMHostsObjs

	def getOrionVIMHostStatistics(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionVIMHostStatisticsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['HostID', 'DateTime', 'VmCount', 'VmRunningCount', 'MinNetworkUtilization', 'MaxNetworkUtilization', 'AvgNetworkUtilization', 'MinNetworkUsageRate', 'MaxNetworkUsageRate', 'AvgNetworkUsageRate', 'MinNetworkTransmitRate', 'MaxNetworkTransmitRate', 'AvgNetworkTransmitRate', 'MinNetworkReceiveRate', 'MaxNetworkReceiveRate', 'AvgNetworkReceiveRate']
		tableName = 'Orion.VIM.HostStatistics'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionVIMHostStatistics = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionVIMHostStatistics == None:
				return []
		for obj in currOrionVIMHostStatistics['results']:
			thisObj = OrionVIMHostStatistics(connection=self,data=obj)
			self.orionVIMHostStatisticsObjs.append(thisObj)
		return self.orionVIMHostStatisticsObjs

	def getOrionVIMManagedEntity(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionVIMManagedEntityObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['Status', 'StatusDescription', 'StatusLED', 'UnManaged', 'UnManageFrom', 'UnManageUntil', 'TriggeredAlarmDescription', 'DetailsUrl', 'Image']
		tableName = 'Orion.VIM.ManagedEntity'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionVIMManagedEntity = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionVIMManagedEntity == None:
				return []
		for obj in currOrionVIMManagedEntity['results']:
			thisObj = OrionVIMManagedEntity(connection=self,data=obj)
			self.orionVIMManagedEntityObjs.append(thisObj)
		return self.orionVIMManagedEntityObjs

	def getOrionVIMResourcePools(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionVIMResourcePoolsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['ResourcePoolID', 'ManagedObjectID', 'Name', 'CpuMaxUsage', 'CpuOverallUsage', 'CpuReservationUsedForVM', 'CpuReservationUsed', 'MemMaxUsage', 'MemOverallUsage', 'MemReservationUsedForVM', 'MemReservationUsed', 'LastModifiedTime', 'CpuExpandable', 'CpuLimit', 'CpuReservation', 'CpuShareLevel', 'CpuShareCount', 'MemExpandable', 'MemLimit', 'MemReservation', 'MemShareLevel', 'MemShareCount', 'ConfigStatus', 'OverallStatus', 'ManagedStatus', 'ClusterID', 'VCenterID', 'ParentResourcePoolID']
		tableName = 'Orion.VIM.ResourcePools'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionVIMResourcePools = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionVIMResourcePools == None:
				return []
		for obj in currOrionVIMResourcePools['results']:
			thisObj = OrionVIMResourcePools(connection=self,data=obj)
			self.orionVIMResourcePoolsObjs.append(thisObj)
		return self.orionVIMResourcePoolsObjs

	def getOrionVIMThresholds(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionVIMThresholdsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['ThresholdID', 'TypeID', 'Warning', 'High', 'Maximum']
		tableName = 'Orion.VIM.Thresholds'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionVIMThresholds = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionVIMThresholds == None:
				return []
		for obj in currOrionVIMThresholds['results']:
			thisObj = OrionVIMThresholds(connection=self,data=obj)
			self.orionVIMThresholdsObjs.append(thisObj)
		return self.orionVIMThresholdsObjs

	def getOrionVIMThresholdTypes(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionVIMThresholdTypesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['TypeID', 'Name', 'Information', 'Warning', 'High', 'Maximum']
		tableName = 'Orion.VIM.ThresholdTypes'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionVIMThresholdTypes = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionVIMThresholdTypes == None:
				return []
		for obj in currOrionVIMThresholdTypes['results']:
			thisObj = OrionVIMThresholdTypes(connection=self,data=obj)
			self.orionVIMThresholdTypesObjs.append(thisObj)
		return self.orionVIMThresholdTypesObjs

	def getOrionVIMVCenters(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionVIMVCentersObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['VCenterID', 'NodeID', 'Name', 'VMwareProductName', 'VMwareProductVersion', 'PollingJobID', 'ServiceURIID', 'CredentialID', 'HostStatus', 'Model', 'Vendor', 'BuildNumber', 'BiosSerial', 'IPAddress', 'ConnectionState', 'StatusMessage']
		tableName = 'Orion.VIM.VCenters'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionVIMVCenters = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionVIMVCenters == None:
				return []
		for obj in currOrionVIMVCenters['results']:
			thisObj = OrionVIMVCenters(connection=self,data=obj)
			self.orionVIMVCentersObjs.append(thisObj)
		return self.orionVIMVCentersObjs

	def getOrionVIMVirtualMachines(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionVIMVirtualMachinesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['VirtualMachineID', 'ManagedObjectID', 'UUID', 'HostID', 'NodeID', 'ResourcePoolID', 'VMConfigFile', 'MemoryConfigured', 'MemoryShares', 'CPUShares', 'GuestState', 'IPAddress', 'LogDirectory', 'GuestVmWareToolsVersion', 'GuestVmWareToolsStatus', 'Name', 'GuestName', 'GuestFamily', 'GuestDnsName', 'NicCount', 'VDisksCount', 'ProcessorCount', 'PowerState', 'BootTime', 'ConfigStatus', 'OverallStatus', 'NodeStatus', 'NetworkUsageRate', 'NetworkTransmitRate', 'NetworkReceiveRate', 'CpuLoad', 'CpuUsageMHz', 'MemUsage', 'MemUsageMB', 'IsLicensed']
		tableName = 'Orion.VIM.VirtualMachines'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionVIMVirtualMachines = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionVIMVirtualMachines == None:
				return []
		for obj in currOrionVIMVirtualMachines['results']:
			thisObj = OrionVIMVirtualMachines(connection=self,data=obj)
			self.orionVIMVirtualMachinesObjs.append(thisObj)
		return self.orionVIMVirtualMachinesObjs

	def getOrionVIMVMStatistics(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionVIMVMStatisticsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['VirtualMachineID', 'DateTime', 'MinCPULoad', 'MaxCPULoad', 'AvgCPULoad', 'MinMemoryUsage', 'MaxMemoryUsage', 'AvgMemoryUsage', 'MinNetworkUsageRate', 'MaxNetworkUsageRate', 'AvgNetworkUsageRate', 'MinNetworkTransmitRate', 'MaxNetworkTransmitRate', 'AvgNetworkTransmitRate', 'MinNetworkReceiveRate', 'MaxNetworkReceiveRate', 'AvgNetworkReceiveRate', 'Availability']
		tableName = 'Orion.VIM.VMStatistics'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionVIMVMStatistics = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionVIMVMStatistics == None:
				return []
		for obj in currOrionVIMVMStatistics['results']:
			thisObj = OrionVIMVMStatistics(connection=self,data=obj)
			self.orionVIMVMStatisticsObjs.append(thisObj)
		return self.orionVIMVMStatisticsObjs

	def getOrionVolumePerformanceHistory(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionVolumePerformanceHistoryObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['NodeID', 'VolumeID', 'DateTime', 'AvgDiskQueueLength', 'MinDiskQueueLength', 'MaxDiskQueueLength', 'AvgDiskTransfer', 'MinDiskTransfer', 'MaxDiskTransfer', 'AvgDiskReads', 'MinDiskReads', 'MaxDiskReads', 'AvgDiskWrites', 'MinDiskWrites', 'MaxDiskWrites']
		tableName = 'Orion.VolumePerformanceHistory'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionVolumePerformanceHistory = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionVolumePerformanceHistory == None:
				return []
		for obj in currOrionVolumePerformanceHistory['results']:
			thisObj = OrionVolumePerformanceHistory(connection=self,data=obj)
			self.orionVolumePerformanceHistoryObjs.append(thisObj)
		return self.orionVolumePerformanceHistoryObjs

	def getOrionVolumes(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionVolumesObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['NodeID', 'VolumeID', 'Icon', 'Index', 'Caption', 'PollInterval', 'StatCollection', 'RediscoveryInterval', 'StatusIcon', 'Type', 'Size', 'Responding', 'FullName', 'LastSync', 'VolumePercentUsed', 'VolumeAllocationFailuresThisHour', 'VolumeIndex', 'VolumeType', 'VolumeDescription', 'VolumeSize', 'VolumeSpaceUsed', 'VolumeAllocationFailuresToday', 'VolumeResponding', 'VolumeSpaceAvailable', 'VolumeTypeIcon', 'OrionIdPrefix', 'OrionIdColumn', 'DiskQueueLength', 'DiskTransfer', 'DiskReads', 'DiskWrites', 'TotalDiskIOPS']
		tableName = 'Orion.Volumes'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionVolumes = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionVolumes == None:
				return []
		for obj in currOrionVolumes['results']:
			thisObj = OrionVolumes(connection=self,data=obj)
			self.orionVolumesObjs.append(thisObj)
		return self.orionVolumesObjs

	def getOrionVolumesStats(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionVolumesStatsObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['PercentUsed', 'SpaceUsed', 'SpaceAvailable', 'AllocationFailuresThisHour', 'AllocationFailuresToday', 'DiskQueueLength', 'DiskTransfer', 'DiskReads', 'DiskWrites', 'TotalDiskIOPS', 'VolumeID']
		tableName = 'Orion.VolumesStats'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionVolumesStats = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionVolumesStats == None:
				return []
		for obj in currOrionVolumesStats['results']:
			thisObj = OrionVolumesStats(connection=self,data=obj)
			self.orionVolumesStatsObjs.append(thisObj)
		return self.orionVolumesStatsObjs

	def getOrionVolumeUsageHistory(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['selectList', 'whereList']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		self.orionVolumeUsageHistoryObjs=[]
		self.selectList=ar['selectList']
		self.whereList=ar['whereList']
		fieldList = ['NodeID', 'VolumeID', 'DateTime', 'DiskSize', 'AvgDiskUsed', 'MinDiskUsed', 'MaxDiskUsed', 'PercentDiskUsed', 'AllocationFailures']
		tableName = 'Orion.VolumeUsageHistory'
		selectQuery = None
		if not ar['selectList'] and not ar['whereList']:
			selectQuery = convertFieldListToSelect(fieldList, tableName)
		elif ar['selectList'] and not ar['whereList']:
			selectQuery = convertSelectListToSelect(fieldList, tableName, ar['selectList'])
		elif not ar['selectList'] and ar['whereList']:
			selectQuery = convertWhereListToWhere(fieldList, tableName, ar['whereList'])
		elif ar['selectList'] and ar['whereList']:
			selectQuery = convertSelectWhereListToSelectWhere(fieldList, tableName, ar['selectList'], ar['whereList'])
		if selectQuery:
			currOrionVolumeUsageHistory = self.sendRequest(Type='GET', URL= '/SolarWinds/InformationService/v3/Json/Query?query=' + selectQuery, status=200)
			if currOrionVolumeUsageHistory == None:
				return []
		for obj in currOrionVolumeUsageHistory['results']:
			thisObj = OrionVolumeUsageHistory(connection=self,data=obj)
			self.orionVolumeUsageHistoryObjs.append(thisObj)
		return self.orionVolumeUsageHistoryObjs

class OrionAccounts():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.accountID=data['AccountID']
		except:
			self.accountID=None
		try:
			self.enabled=data['Enabled']
		except:
			self.enabled=None
		try:
			self.allowNodeManagement=data['AllowNodeManagement']
		except:
			self.allowNodeManagement=None
		try:
			self.allowAdmin=data['AllowAdmin']
		except:
			self.allowAdmin=None
		try:
			self.canClearEvents=data['CanClearEvents']
		except:
			self.canClearEvents=None
		try:
			self.allowReportManagement=data['AllowReportManagement']
		except:
			self.allowReportManagement=None
		try:
			self.expires=data['Expires']
		except:
			self.expires=None
		try:
			self.lastLogin=data['LastLogin']
		except:
			self.lastLogin=None
		try:
			self.limitationID1=data['LimitationID1']
		except:
			self.limitationID1=None
		try:
			self.limitationID2=data['LimitationID2']
		except:
			self.limitationID2=None
		try:
			self.limitationID3=data['LimitationID3']
		except:
			self.limitationID3=None
		try:
			self.accountSID=data['AccountSID']
		except:
			self.accountSID=None
		try:
			self.accountType=data['AccountType']
		except:
			self.accountType=None

	def getAccountID(self):
		return self.accountID
	def getEnabled(self):
		return self.enabled
	def getAllowNodeManagement(self):
		return self.allowNodeManagement
	def getAllowAdmin(self):
		return self.allowAdmin
	def getCanClearEvents(self):
		return self.canClearEvents
	def getAllowReportManagement(self):
		return self.allowReportManagement
	def getExpires(self):
		return self.expires
	def getLastLogin(self):
		return self.lastLogin
	def getLimitationID1(self):
		return self.limitationID1
	def getLimitationID2(self):
		return self.limitationID2
	def getLimitationID3(self):
		return self.limitationID3
	def getAccountSID(self):
		return self.accountSID
	def getAccountType(self):
		return self.accountType

class OrionActiveAlerts():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.alertID=data['AlertID']
		except:
			self.alertID=None
		try:
			self.alertTime=data['AlertTime']
		except:
			self.alertTime=None
		try:
			self.objectType=data['ObjectType']
		except:
			self.objectType=None
		try:
			self.objectID=data['ObjectID']
		except:
			self.objectID=None
		try:
			self.objectName=data['ObjectName']
		except:
			self.objectName=None
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.nodeName=data['NodeName']
		except:
			self.nodeName=None
		try:
			self.eventMessage=data['EventMessage']
		except:
			self.eventMessage=None
		try:
			self.propertyID=data['propertyID']
		except:
			self.propertyID=None
		try:
			self.monitoredproperty=data['Monitoredproperty']
		except:
			self.monitoredproperty=None
		try:
			self.currentValue=data['CurrentValue']
		except:
			self.currentValue=None
		try:
			self.triggerValue=data['TriggerValue']
		except:
			self.triggerValue=None
		try:
			self.resetValue=data['ResetValue']
		except:
			self.resetValue=None
		try:
			self.engineID=data['EngineID']
		except:
			self.engineID=None
		try:
			self.alertNotes=data['AlertNotes']
		except:
			self.alertNotes=None
		try:
			self.expireTime=data['ExpireTime']
		except:
			self.expireTime=None

	def getAlertID(self):
		return self.alertID
	def getAlertTime(self):
		return self.alertTime
	def getObjectType(self):
		return self.objectType
	def getObjectID(self):
		return self.objectID
	def getObjectName(self):
		return self.objectName
	def getNodeID(self):
		return self.nodeID
	def getNodeName(self):
		return self.nodeName
	def getEventMessage(self):
		return self.eventMessage
	def getpropertyID(self):
		return self.propertyID
	def getMonitoredproperty(self):
		return self.monitoredproperty
	def getCurrentValue(self):
		return self.currentValue
	def getTriggerValue(self):
		return self.triggerValue
	def getResetValue(self):
		return self.resetValue
	def getEngineID(self):
		return self.engineID
	def getAlertNotes(self):
		return self.alertNotes
	def getExpireTime(self):
		return self.expireTime

class OrionAlertDefinitions():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.alertDefID=data['AlertDefID']
		except:
			self.alertDefID=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.description=data['Description']
		except:
			self.description=None
		try:
			self.enabled=data['Enabled']
		except:
			self.enabled=None
		try:
			self.startTime=data['StartTime']
		except:
			self.startTime=None
		try:
			self.endTime=data['EndTime']
		except:
			self.endTime=None
		try:
			self.dOW=data['DOW']
		except:
			self.dOW=None
		try:
			self.triggerQuery=data['TriggerQuery']
		except:
			self.triggerQuery=None
		try:
			self.triggerQueryDesign=data['TriggerQueryDesign']
		except:
			self.triggerQueryDesign=None
		try:
			self.resetQuery=data['ResetQuery']
		except:
			self.resetQuery=None
		try:
			self.resetQueryDesign=data['ResetQueryDesign']
		except:
			self.resetQueryDesign=None
		try:
			self.suppressionQuery=data['SuppressionQuery']
		except:
			self.suppressionQuery=None
		try:
			self.suppressionQueryDesign=data['SuppressionQueryDesign']
		except:
			self.suppressionQueryDesign=None
		try:
			self.triggerSustained=data['TriggerSustained']
		except:
			self.triggerSustained=None
		try:
			self.resetSustained=data['ResetSustained']
		except:
			self.resetSustained=None
		try:
			self.lastExecuteTime=data['LastExecuteTime']
		except:
			self.lastExecuteTime=None
		try:
			self.executeInterval=data['ExecuteInterval']
		except:
			self.executeInterval=None
		try:
			self.blockUntil=data['BlockUntil']
		except:
			self.blockUntil=None
		try:
			self.responseTime=data['ResponseTime']
		except:
			self.responseTime=None
		try:
			self.lastErrorTime=data['LastErrorTime']
		except:
			self.lastErrorTime=None
		try:
			self.lastError=data['LastError']
		except:
			self.lastError=None
		try:
			self.objectType=data['ObjectType']
		except:
			self.objectType=None

	def getAlertDefID(self):
		return self.alertDefID
	def getName(self):
		return self.name
	def getDescription(self):
		return self.description
	def getEnabled(self):
		return self.enabled
	def getStartTime(self):
		return self.startTime
	def getEndTime(self):
		return self.endTime
	def getDOW(self):
		return self.dOW
	def getTriggerQuery(self):
		return self.triggerQuery
	def getTriggerQueryDesign(self):
		return self.triggerQueryDesign
	def getResetQuery(self):
		return self.resetQuery
	def getResetQueryDesign(self):
		return self.resetQueryDesign
	def getSuppressionQuery(self):
		return self.suppressionQuery
	def getSuppressionQueryDesign(self):
		return self.suppressionQueryDesign
	def getTriggerSustained(self):
		return self.triggerSustained
	def getResetSustained(self):
		return self.resetSustained
	def getLastExecuteTime(self):
		return self.lastExecuteTime
	def getExecuteInterval(self):
		return self.executeInterval
	def getBlockUntil(self):
		return self.blockUntil
	def getResponseTime(self):
		return self.responseTime
	def getLastErrorTime(self):
		return self.lastErrorTime
	def getLastError(self):
		return self.lastError
	def getObjectType(self):
		return self.objectType

class OrionAlerts():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.engineID=data['EngineID']
		except:
			self.engineID=None
		try:
			self.alertID=data['AlertID']
		except:
			self.alertID=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.enabled=data['Enabled']
		except:
			self.enabled=None
		try:
			self.description=data['Description']
		except:
			self.description=None
		try:
			self.startTime=data['StartTime']
		except:
			self.startTime=None
		try:
			self.endTime=data['EndTime']
		except:
			self.endTime=None
		try:
			self.dOW=data['DOW']
		except:
			self.dOW=None
		try:
			self.netObjects=data['NetObjects']
		except:
			self.netObjects=None
		try:
			self.propertyID=data['propertyID']
		except:
			self.propertyID=None
		try:
			self.trigger=data['Trigger']
		except:
			self.trigger=None
		try:
			self.reset=data['Reset']
		except:
			self.reset=None
		try:
			self.sustained=data['Sustained']
		except:
			self.sustained=None
		try:
			self.triggerSubjectTemplate=data['TriggerSubjectTemplate']
		except:
			self.triggerSubjectTemplate=None
		try:
			self.triggerMessageTemplate=data['TriggerMessageTemplate']
		except:
			self.triggerMessageTemplate=None
		try:
			self.resetSubjectTemplate=data['ResetSubjectTemplate']
		except:
			self.resetSubjectTemplate=None
		try:
			self.resetMessageTemplate=data['ResetMessageTemplate']
		except:
			self.resetMessageTemplate=None
		try:
			self.frequency=data['Frequency']
		except:
			self.frequency=None
		try:
			self.eMailAddresses=data['EMailAddresses']
		except:
			self.eMailAddresses=None
		try:
			self.replyName=data['ReplyName']
		except:
			self.replyName=None
		try:
			self.replyAddress=data['ReplyAddress']
		except:
			self.replyAddress=None
		try:
			self.logFile=data['LogFile']
		except:
			self.logFile=None
		try:
			self.logMessage=data['LogMessage']
		except:
			self.logMessage=None
		try:
			self.shellTrigger=data['ShellTrigger']
		except:
			self.shellTrigger=None
		try:
			self.shellReset=data['ShellReset']
		except:
			self.shellReset=None
		try:
			self.suppressionType=data['SuppressionType']
		except:
			self.suppressionType=None
		try:
			self.suppression=data['Suppression']
		except:
			self.suppression=None

	def getEngineID(self):
		return self.engineID
	def getAlertID(self):
		return self.alertID
	def getName(self):
		return self.name
	def getEnabled(self):
		return self.enabled
	def getDescription(self):
		return self.description
	def getStartTime(self):
		return self.startTime
	def getEndTime(self):
		return self.endTime
	def getDOW(self):
		return self.dOW
	def getNetObjects(self):
		return self.netObjects
	def getpropertyID(self):
		return self.propertyID
	def getTrigger(self):
		return self.trigger
	def getReset(self):
		return self.reset
	def getSustained(self):
		return self.sustained
	def getTriggerSubjectTemplate(self):
		return self.triggerSubjectTemplate
	def getTriggerMessageTemplate(self):
		return self.triggerMessageTemplate
	def getResetSubjectTemplate(self):
		return self.resetSubjectTemplate
	def getResetMessageTemplate(self):
		return self.resetMessageTemplate
	def getFrequency(self):
		return self.frequency
	def getEMailAddresses(self):
		return self.eMailAddresses
	def getReplyName(self):
		return self.replyName
	def getReplyAddress(self):
		return self.replyAddress
	def getLogFile(self):
		return self.logFile
	def getLogMessage(self):
		return self.logMessage
	def getShellTrigger(self):
		return self.shellTrigger
	def getShellReset(self):
		return self.shellReset
	def getSuppressionType(self):
		return self.suppressionType
	def getSuppression(self):
		return self.suppression

class OrionAlertStatus():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.alertDefID=data['AlertDefID']
		except:
			self.alertDefID=None
		try:
			self.activeObject=data['ActiveObject']
		except:
			self.activeObject=None
		try:
			self.objectType=data['ObjectType']
		except:
			self.objectType=None
		try:
			self.state=data['State']
		except:
			self.state=None
		try:
			self.workingState=data['WorkingState']
		except:
			self.workingState=None
		try:
			self.objectName=data['ObjectName']
		except:
			self.objectName=None
		try:
			self.alertMessage=data['AlertMessage']
		except:
			self.alertMessage=None
		try:
			self.triggerTimeStamp=data['TriggerTimeStamp']
		except:
			self.triggerTimeStamp=None
		try:
			self.triggerTimeOffset=data['TriggerTimeOffset']
		except:
			self.triggerTimeOffset=None
		try:
			self.triggerCount=data['TriggerCount']
		except:
			self.triggerCount=None
		try:
			self.resetTimeStamp=data['ResetTimeStamp']
		except:
			self.resetTimeStamp=None
		try:
			self.acknowledged=data['Acknowledged']
		except:
			self.acknowledged=None
		try:
			self.acknowledgedBy=data['AcknowledgedBy']
		except:
			self.acknowledgedBy=None
		try:
			self.acknowledgedTime=data['AcknowledgedTime']
		except:
			self.acknowledgedTime=None
		try:
			self.lastUpdate=data['LastUpdate']
		except:
			self.lastUpdate=None
		try:
			self.alertNotes=data['AlertNotes']
		except:
			self.alertNotes=None
		try:
			self.notes=data['Notes']
		except:
			self.notes=None

	def getAlertDefID(self):
		return self.alertDefID
	def getActiveObject(self):
		return self.activeObject
	def getObjectType(self):
		return self.objectType
	def getState(self):
		return self.state
	def getWorkingState(self):
		return self.workingState
	def getObjectName(self):
		return self.objectName
	def getAlertMessage(self):
		return self.alertMessage
	def getTriggerTimeStamp(self):
		return self.triggerTimeStamp
	def getTriggerTimeOffset(self):
		return self.triggerTimeOffset
	def getTriggerCount(self):
		return self.triggerCount
	def getResetTimeStamp(self):
		return self.resetTimeStamp
	def getAcknowledged(self):
		return self.acknowledged
	def getAcknowledgedBy(self):
		return self.acknowledgedBy
	def getAcknowledgedTime(self):
		return self.acknowledgedTime
	def getLastUpdate(self):
		return self.lastUpdate
	def getAlertNotes(self):
		return self.alertNotes
	def getNotes(self):
		return self.notes

class OrionAuditingActionTypes():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.actionTypeID=data['ActionTypeID']
		except:
			self.actionTypeID=None
		try:
			self.actionType=data['ActionType']
		except:
			self.actionType=None
		try:
			self.actionTypeDisplayName=data['ActionTypeDisplayName']
		except:
			self.actionTypeDisplayName=None

	def getActionTypeID(self):
		return self.actionTypeID
	def getActionType(self):
		return self.actionType
	def getActionTypeDisplayName(self):
		return self.actionTypeDisplayName

class OrionAuditingArguments():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.auditEventID=data['AuditEventID']
		except:
			self.auditEventID=None
		try:
			self.argsKey=data['ArgsKey']
		except:
			self.argsKey=None
		try:
			self.argsValue=data['ArgsValue']
		except:
			self.argsValue=None

	def getAuditEventID(self):
		return self.auditEventID
	def getArgsKey(self):
		return self.argsKey
	def getArgsValue(self):
		return self.argsValue

class OrionAuditingEvents():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.auditEventID=data['AuditEventID']
		except:
			self.auditEventID=None
		try:
			self.timeLoggedUtc=data['TimeLoggedUtc']
		except:
			self.timeLoggedUtc=None
		try:
			self.accountID=data['AccountID']
		except:
			self.accountID=None
		try:
			self.actionTypeID=data['ActionTypeID']
		except:
			self.actionTypeID=None
		try:
			self.auditEventMessage=data['AuditEventMessage']
		except:
			self.auditEventMessage=None
		try:
			self.networkNode=data['NetworkNode']
		except:
			self.networkNode=None
		try:
			self.netObjectID=data['NetObjectID']
		except:
			self.netObjectID=None
		try:
			self.netObjectType=data['NetObjectType']
		except:
			self.netObjectType=None

	def getAuditEventID(self):
		return self.auditEventID
	def getTimeLoggedUtc(self):
		return self.timeLoggedUtc
	def getAccountID(self):
		return self.accountID
	def getActionTypeID(self):
		return self.actionTypeID
	def getAuditEventMessage(self):
		return self.auditEventMessage
	def getNetworkNode(self):
		return self.networkNode
	def getNetObjectID(self):
		return self.netObjectID
	def getNetObjectType(self):
		return self.netObjectType

class OrionContainer():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.containerID=data['ContainerID']
		except:
			self.containerID=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.owner=data['Owner']
		except:
			self.owner=None
		try:
			self.frequency=data['Frequency']
		except:
			self.frequency=None
		try:
			self.statusCalculator=data['StatusCalculator']
		except:
			self.statusCalculator=None
		try:
			self.rollupType=data['RollupType']
		except:
			self.rollupType=None
		try:
			self.isDeleted=data['IsDeleted']
		except:
			self.isDeleted=None
		try:
			self.pollingEnabled=data['PollingEnabled']
		except:
			self.pollingEnabled=None
		try:
			self.lastChanged=data['LastChanged']
		except:
			self.lastChanged=None

	def getContainerID(self):
		return self.containerID
	def getName(self):
		return self.name
	def getOwner(self):
		return self.owner
	def getFrequency(self):
		return self.frequency
	def getStatusCalculator(self):
		return self.statusCalculator
	def getRollupType(self):
		return self.rollupType
	def getIsDeleted(self):
		return self.isDeleted
	def getPollingEnabled(self):
		return self.pollingEnabled
	def getLastChanged(self):
		return self.lastChanged

class OrionContainerMemberDefinition():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.definitionID=data['DefinitionID']
		except:
			self.definitionID=None
		try:
			self.containerID=data['ContainerID']
		except:
			self.containerID=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.entity=data['Entity']
		except:
			self.entity=None
		try:
			self.fromClause=data['FromClause']
		except:
			self.fromClause=None
		try:
			self.expression=data['Expression']
		except:
			self.expression=None
		try:
			self.definition=data['Definition']
		except:
			self.definition=None

	def getDefinitionID(self):
		return self.definitionID
	def getContainerID(self):
		return self.containerID
	def getName(self):
		return self.name
	def getEntity(self):
		return self.entity
	def getFromClause(self):
		return self.fromClause
	def getExpression(self):
		return self.expression
	def getDefinition(self):
		return self.definition

class OrionContainerMembers():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.containerID=data['ContainerID']
		except:
			self.containerID=None
		try:
			self.memberPrimaryID=data['MemberPrimaryID']
		except:
			self.memberPrimaryID=None
		try:
			self.memberEntityType=data['MemberEntityType']
		except:
			self.memberEntityType=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.status=data['Status']
		except:
			self.status=None
		try:
			self.memberUri=data['MemberUri']
		except:
			self.memberUri=None
		try:
			self.memberAncestorDisplayNames=data['MemberAncestorDisplayNames']
		except:
			self.memberAncestorDisplayNames=None
		try:
			self.memberAncestorDetailsUrls=data['MemberAncestorDetailsUrls']
		except:
			self.memberAncestorDetailsUrls=None

	def getContainerID(self):
		return self.containerID
	def getMemberPrimaryID(self):
		return self.memberPrimaryID
	def getMemberEntityType(self):
		return self.memberEntityType
	def getName(self):
		return self.name
	def getStatus(self):
		return self.status
	def getMemberUri(self):
		return self.memberUri
	def getMemberAncestorDisplayNames(self):
		return self.memberAncestorDisplayNames
	def getMemberAncestorDetailsUrls(self):
		return self.memberAncestorDetailsUrls

class OrionContainerMemberSnapshots():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.containerMemberSnapshotID=data['ContainerMemberSnapshotID']
		except:
			self.containerMemberSnapshotID=None
		try:
			self.containerID=data['ContainerID']
		except:
			self.containerID=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.fullName=data['FullName']
		except:
			self.fullName=None
		try:
			self.entityDisplayName=data['EntityDisplayName']
		except:
			self.entityDisplayName=None
		try:
			self.entityDisplayNamePlural=data['EntityDisplayNamePlural']
		except:
			self.entityDisplayNamePlural=None
		try:
			self.memberUri=data['MemberUri']
		except:
			self.memberUri=None
		try:
			self.status=data['Status']
		except:
			self.status=None

	def getContainerMemberSnapshotID(self):
		return self.containerMemberSnapshotID
	def getContainerID(self):
		return self.containerID
	def getName(self):
		return self.name
	def getFullName(self):
		return self.fullName
	def getEntityDisplayName(self):
		return self.entityDisplayName
	def getEntityDisplayNamePlural(self):
		return self.entityDisplayNamePlural
	def getMemberUri(self):
		return self.memberUri
	def getStatus(self):
		return self.status

class OrionCPUMultiLoad():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.timeStampUTC=data['TimeStampUTC']
		except:
			self.timeStampUTC=None
		try:
			self.cPUIndex=data['CPUIndex']
		except:
			self.cPUIndex=None
		try:
			self.minLoad=data['MinLoad']
		except:
			self.minLoad=None
		try:
			self.maxLoad=data['MaxLoad']
		except:
			self.maxLoad=None
		try:
			self.avgLoad=data['AvgLoad']
		except:
			self.avgLoad=None

	def getNodeID(self):
		return self.nodeID
	def getTimeStampUTC(self):
		return self.timeStampUTC
	def getCPUIndex(self):
		return self.cPUIndex
	def getMinLoad(self):
		return self.minLoad
	def getMaxLoad(self):
		return self.maxLoad
	def getAvgLoad(self):
		return self.avgLoad

class OrionCredential():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.iD=data['ID']
		except:
			self.iD=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.description=data['Description']
		except:
			self.description=None
		try:
			self.credentialType=data['CredentialType']
		except:
			self.credentialType=None
		try:
			self.credentialOwner=data['CredentialOwner']
		except:
			self.credentialOwner=None

	def getID(self):
		return self.iD
	def getName(self):
		return self.name
	def getDescription(self):
		return self.description
	def getCredentialType(self):
		return self.credentialType
	def getCredentialOwner(self):
		return self.credentialOwner

class OrionCustomProperty():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.table=data['Table']
		except:
			self.table=None
		try:
			self.field=data['Field']
		except:
			self.field=None
		try:
			self.dataType=data['DataType']
		except:
			self.dataType=None
		try:
			self.maxLength=data['MaxLength']
		except:
			self.maxLength=None
		try:
			self.storageMethod=data['StorageMethod']
		except:
			self.storageMethod=None
		try:
			self.description=data['Description']
		except:
			self.description=None
		try:
			self.targetEntity=data['TargetEntity']
		except:
			self.targetEntity=None

	def getTable(self):
		return self.table
	def getField(self):
		return self.field
	def getDataType(self):
		return self.dataType
	def getMaxLength(self):
		return self.maxLength
	def getStorageMethod(self):
		return self.storageMethod
	def getDescription(self):
		return self.description
	def getTargetEntity(self):
		return self.targetEntity

class OrionCustomPropertyUsage():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.table=data['Table']
		except:
			self.table=None
		try:
			self.field=data['Field']
		except:
			self.field=None
		try:
			self.isForAlerting=data['IsForAlerting']
		except:
			self.isForAlerting=None
		try:
			self.isForFiltering=data['IsForFiltering']
		except:
			self.isForFiltering=None
		try:
			self.isForGrouping=data['IsForGrouping']
		except:
			self.isForGrouping=None
		try:
			self.isForReporting=data['IsForReporting']
		except:
			self.isForReporting=None
		try:
			self.isForEntityDetail=data['IsForEntityDetail']
		except:
			self.isForEntityDetail=None

	def getTable(self):
		return self.table
	def getField(self):
		return self.field
	def getIsForAlerting(self):
		return self.isForAlerting
	def getIsForFiltering(self):
		return self.isForFiltering
	def getIsForGrouping(self):
		return self.isForGrouping
	def getIsForReporting(self):
		return self.isForReporting
	def getIsForEntityDetail(self):
		return self.isForEntityDetail

class OrionCustomPropertyValues():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.table=data['Table']
		except:
			self.table=None
		try:
			self.field=data['Field']
		except:
			self.field=None
		try:
			self.value=data['Value']
		except:
			self.value=None

	def getTable(self):
		return self.table
	def getField(self):
		return self.field
	def getValue(self):
		return self.value

class OrionDependencies():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.dependencyId=data['DependencyId']
		except:
			self.dependencyId=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.parentUri=data['ParentUri']
		except:
			self.parentUri=None
		try:
			self.childUri=data['ChildUri']
		except:
			self.childUri=None
		try:
			self.lastUpdateUTC=data['LastUpdateUTC']
		except:
			self.lastUpdateUTC=None

	def getDependencyId(self):
		return self.dependencyId
	def getName(self):
		return self.name
	def getParentUri(self):
		return self.parentUri
	def getChildUri(self):
		return self.childUri
	def getLastUpdateUTC(self):
		return self.lastUpdateUTC

class OrionDependencyEntities():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.entityName=data['EntityName']
		except:
			self.entityName=None
		try:
			self.validParent=data['ValidParent']
		except:
			self.validParent=None
		try:
			self.validChild=data['ValidChild']
		except:
			self.validChild=None

	def getEntityName(self):
		return self.entityName
	def getValidParent(self):
		return self.validParent
	def getValidChild(self):
		return self.validChild

class OrionDiscoveredNodes():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.profileID=data['ProfileID']
		except:
			self.profileID=None
		try:
			self.iPAddress=data['IPAddress']
		except:
			self.iPAddress=None
		try:
			self.iPAddressGUID=data['IPAddressGUID']
		except:
			self.iPAddressGUID=None
		try:
			self.snmpVersion=data['SnmpVersion']
		except:
			self.snmpVersion=None
		try:
			self.subType=data['SubType']
		except:
			self.subType=None
		try:
			self.credentialID=data['CredentialID']
		except:
			self.credentialID=None
		try:
			self.hostname=data['Hostname']
		except:
			self.hostname=None
		try:
			self.dNS=data['DNS']
		except:
			self.dNS=None
		try:
			self.sysObjectID=data['SysObjectID']
		except:
			self.sysObjectID=None
		try:
			self.vendor=data['Vendor']
		except:
			self.vendor=None
		try:
			self.vendorIcon=data['VendorIcon']
		except:
			self.vendorIcon=None
		try:
			self.machineType=data['MachineType']
		except:
			self.machineType=None
		try:
			self.sysDescription=data['SysDescription']
		except:
			self.sysDescription=None
		try:
			self.sysName=data['SysName']
		except:
			self.sysName=None
		try:
			self.location=data['Location']
		except:
			self.location=None
		try:
			self.contact=data['Contact']
		except:
			self.contact=None
		try:
			self.ignoredNodeID=data['IgnoredNodeID']
		except:
			self.ignoredNodeID=None

	def getNodeID(self):
		return self.nodeID
	def getProfileID(self):
		return self.profileID
	def getIPAddress(self):
		return self.iPAddress
	def getIPAddressGUID(self):
		return self.iPAddressGUID
	def getSnmpVersion(self):
		return self.snmpVersion
	def getSubType(self):
		return self.subType
	def getCredentialID(self):
		return self.credentialID
	def getHostname(self):
		return self.hostname
	def getDNS(self):
		return self.dNS
	def getSysObjectID(self):
		return self.sysObjectID
	def getVendor(self):
		return self.vendor
	def getVendorIcon(self):
		return self.vendorIcon
	def getMachineType(self):
		return self.machineType
	def getSysDescription(self):
		return self.sysDescription
	def getSysName(self):
		return self.sysName
	def getLocation(self):
		return self.location
	def getContact(self):
		return self.contact
	def getIgnoredNodeID(self):
		return self.ignoredNodeID

class OrionDiscoveredPollers():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.iD=data['ID']
		except:
			self.iD=None
		try:
			self.profileID=data['ProfileID']
		except:
			self.profileID=None
		try:
			self.netObjectID=data['NetObjectID']
		except:
			self.netObjectID=None
		try:
			self.netObjectType=data['NetObjectType']
		except:
			self.netObjectType=None
		try:
			self.pollerType=data['PollerType']
		except:
			self.pollerType=None

	def getID(self):
		return self.iD
	def getProfileID(self):
		return self.profileID
	def getNetObjectID(self):
		return self.netObjectID
	def getNetObjectType(self):
		return self.netObjectType
	def getPollerType(self):
		return self.pollerType

class OrionDiscoveredVolumes():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.profileID=data['ProfileID']
		except:
			self.profileID=None
		try:
			self.discoveredNodeID=data['DiscoveredNodeID']
		except:
			self.discoveredNodeID=None
		try:
			self.volumeIndex=data['VolumeIndex']
		except:
			self.volumeIndex=None
		try:
			self.volumeType=data['VolumeType']
		except:
			self.volumeType=None
		try:
			self.volumeDescription=data['VolumeDescription']
		except:
			self.volumeDescription=None
		try:
			self.ignoredVolumeID=data['IgnoredVolumeID']
		except:
			self.ignoredVolumeID=None

	def getProfileID(self):
		return self.profileID
	def getDiscoveredNodeID(self):
		return self.discoveredNodeID
	def getVolumeIndex(self):
		return self.volumeIndex
	def getVolumeType(self):
		return self.volumeType
	def getVolumeDescription(self):
		return self.volumeDescription
	def getIgnoredVolumeID(self):
		return self.ignoredVolumeID

class OrionDiscoveryProfiles():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.profileID=data['ProfileID']
		except:
			self.profileID=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.description=data['Description']
		except:
			self.description=None
		try:
			self.runTimeInSeconds=data['RunTimeInSeconds']
		except:
			self.runTimeInSeconds=None
		try:
			self.lastRun=data['LastRun']
		except:
			self.lastRun=None
		try:
			self.engineID=data['EngineID']
		except:
			self.engineID=None
		try:
			self.status=data['Status']
		except:
			self.status=None
		try:
			self.jobID=data['JobID']
		except:
			self.jobID=None
		try:
			self.sIPPort=data['SIPPort']
		except:
			self.sIPPort=None
		try:
			self.hopCount=data['HopCount']
		except:
			self.hopCount=None
		try:
			self.searchTimeout=data['SearchTimeout']
		except:
			self.searchTimeout=None
		try:
			self.sNMPTimeout=data['SNMPTimeout']
		except:
			self.sNMPTimeout=None
		try:
			self.sNMPRetries=data['SNMPRetries']
		except:
			self.sNMPRetries=None
		try:
			self.repeatInterval=data['RepeatInterval']
		except:
			self.repeatInterval=None
		try:
			self.active=data['Active']
		except:
			self.active=None
		try:
			self.duplicateNodes=data['DuplicateNodes']
		except:
			self.duplicateNodes=None
		try:
			self.importUpInterface=data['ImportUpInterface']
		except:
			self.importUpInterface=None
		try:
			self.importDownInterface=data['ImportDownInterface']
		except:
			self.importDownInterface=None
		try:
			self.importShutdownInterface=data['ImportShutdownInterface']
		except:
			self.importShutdownInterface=None
		try:
			self.selectionMethod=data['SelectionMethod']
		except:
			self.selectionMethod=None
		try:
			self.jobTimeout=data['JobTimeout']
		except:
			self.jobTimeout=None
		try:
			self.scheduleRunAtTime=data['ScheduleRunAtTime']
		except:
			self.scheduleRunAtTime=None
		try:
			self.scheduleRunFrequency=data['ScheduleRunFrequency']
		except:
			self.scheduleRunFrequency=None
		try:
			self.statusDescription=data['StatusDescription']
		except:
			self.statusDescription=None
		try:
			self.isHidden=data['IsHidden']
		except:
			self.isHidden=None
		try:
			self.isAutoImport=data['IsAutoImport']
		except:
			self.isAutoImport=None

	def getProfileID(self):
		return self.profileID
	def getName(self):
		return self.name
	def getDescription(self):
		return self.description
	def getRunTimeInSeconds(self):
		return self.runTimeInSeconds
	def getLastRun(self):
		return self.lastRun
	def getEngineID(self):
		return self.engineID
	def getStatus(self):
		return self.status
	def getJobID(self):
		return self.jobID
	def getSIPPort(self):
		return self.sIPPort
	def getHopCount(self):
		return self.hopCount
	def getSearchTimeout(self):
		return self.searchTimeout
	def getSNMPTimeout(self):
		return self.sNMPTimeout
	def getSNMPRetries(self):
		return self.sNMPRetries
	def getRepeatInterval(self):
		return self.repeatInterval
	def getActive(self):
		return self.active
	def getDuplicateNodes(self):
		return self.duplicateNodes
	def getImportUpInterface(self):
		return self.importUpInterface
	def getImportDownInterface(self):
		return self.importDownInterface
	def getImportShutdownInterface(self):
		return self.importShutdownInterface
	def getSelectionMethod(self):
		return self.selectionMethod
	def getJobTimeout(self):
		return self.jobTimeout
	def getScheduleRunAtTime(self):
		return self.scheduleRunAtTime
	def getScheduleRunFrequency(self):
		return self.scheduleRunFrequency
	def getStatusDescription(self):
		return self.statusDescription
	def getIsHidden(self):
		return self.isHidden
	def getIsAutoImport(self):
		return self.isAutoImport

class OrionElementInfo():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.elementType=data['ElementType']
		except:
			self.elementType=None
		try:
			self.maxElementCount=data['MaxElementCount']
		except:
			self.maxElementCount=None

	def getElementType(self):
		return self.elementType
	def getMaxElementCount(self):
		return self.maxElementCount

class OrionEvents():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.eventID=data['EventID']
		except:
			self.eventID=None
		try:
			self.eventTime=data['EventTime']
		except:
			self.eventTime=None
		try:
			self.networkNode=data['NetworkNode']
		except:
			self.networkNode=None
		try:
			self.netObjectID=data['NetObjectID']
		except:
			self.netObjectID=None
		try:
			self.eventType=data['EventType']
		except:
			self.eventType=None
		try:
			self.message=data['Message']
		except:
			self.message=None
		try:
			self.acknowledged=data['Acknowledged']
		except:
			self.acknowledged=None
		try:
			self.netObjectType=data['NetObjectType']
		except:
			self.netObjectType=None
		try:
			self.timeStamp=data['TimeStamp']
		except:
			self.timeStamp=None

	def getEventID(self):
		return self.eventID
	def getEventTime(self):
		return self.eventTime
	def getNetworkNode(self):
		return self.networkNode
	def getNetObjectID(self):
		return self.netObjectID
	def getEventType(self):
		return self.eventType
	def getMessage(self):
		return self.message
	def getAcknowledged(self):
		return self.acknowledged
	def getNetObjectType(self):
		return self.netObjectType
	def getTimeStamp(self):
		return self.timeStamp

class OrionEventTypes():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.eventType=data['EventType']
		except:
			self.eventType=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.bold=data['Bold']
		except:
			self.bold=None
		try:
			self.backColor=data['BackColor']
		except:
			self.backColor=None
		try:
			self.icon=data['Icon']
		except:
			self.icon=None
		try:
			self.sort=data['Sort']
		except:
			self.sort=None
		try:
			self.notify=data['Notify']
		except:
			self.notify=None
		try:
			self.record=data['Record']
		except:
			self.record=None
		try:
			self.sound=data['Sound']
		except:
			self.sound=None
		try:
			self.mute=data['Mute']
		except:
			self.mute=None
		try:
			self.notifyMessage=data['NotifyMessage']
		except:
			self.notifyMessage=None
		try:
			self.notifySubject=data['NotifySubject']
		except:
			self.notifySubject=None

	def getEventType(self):
		return self.eventType
	def getName(self):
		return self.name
	def getBold(self):
		return self.bold
	def getBackColor(self):
		return self.backColor
	def getIcon(self):
		return self.icon
	def getSort(self):
		return self.sort
	def getNotify(self):
		return self.notify
	def getRecord(self):
		return self.record
	def getSound(self):
		return self.sound
	def getMute(self):
		return self.mute
	def getNotifyMessage(self):
		return self.notifyMessage
	def getNotifySubject(self):
		return self.notifySubject

class OrionNodeIPAddresses():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.iPAddress=data['IPAddress']
		except:
			self.iPAddress=None
		try:
			self.iPAddressN=data['IPAddressN']
		except:
			self.iPAddressN=None
		try:
			self.iPAddressType=data['IPAddressType']
		except:
			self.iPAddressType=None
		try:
			self.interfaceIndex=data['InterfaceIndex']
		except:
			self.interfaceIndex=None

	def getNodeID(self):
		return self.nodeID
	def getIPAddress(self):
		return self.iPAddress
	def getIPAddressN(self):
		return self.iPAddressN
	def getIPAddressType(self):
		return self.iPAddressType
	def getInterfaceIndex(self):
		return self.interfaceIndex

class OrionNodeL2Connections():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.portID=data['PortID']
		except:
			self.portID=None
		try:
			self.mACAddress=data['MACAddress']
		except:
			self.mACAddress=None
		try:
			self.status=data['Status']
		except:
			self.status=None
		try:
			self.vlanId=data['VlanId']
		except:
			self.vlanId=None

	def getNodeID(self):
		return self.nodeID
	def getPortID(self):
		return self.portID
	def getMACAddress(self):
		return self.mACAddress
	def getStatus(self):
		return self.status
	def getVlanId(self):
		return self.vlanId

class OrionNodeL3Entries():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.ifIndex=data['IfIndex']
		except:
			self.ifIndex=None
		try:
			self.mACAddress=data['MACAddress']
		except:
			self.mACAddress=None
		try:
			self.iPAddress=data['IPAddress']
		except:
			self.iPAddress=None
		try:
			self.type=data['Type']
		except:
			self.type=None

	def getNodeID(self):
		return self.nodeID
	def getIfIndex(self):
		return self.ifIndex
	def getMACAddress(self):
		return self.mACAddress
	def getIPAddress(self):
		return self.iPAddress
	def getType(self):
		return self.type

class OrionNodeLldpEntry():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.localPortNumber=data['LocalPortNumber']
		except:
			self.localPortNumber=None
		try:
			self.remoteIfIndex=data['RemoteIfIndex']
		except:
			self.remoteIfIndex=None
		try:
			self.remotePortId=data['RemotePortId']
		except:
			self.remotePortId=None
		try:
			self.remotePortDescription=data['RemotePortDescription']
		except:
			self.remotePortDescription=None
		try:
			self.remoteSystemName=data['RemoteSystemName']
		except:
			self.remoteSystemName=None
		try:
			self.remoteIpAddress=data['RemoteIpAddress']
		except:
			self.remoteIpAddress=None

	def getNodeID(self):
		return self.nodeID
	def getLocalPortNumber(self):
		return self.localPortNumber
	def getRemoteIfIndex(self):
		return self.remoteIfIndex
	def getRemotePortId(self):
		return self.remotePortId
	def getRemotePortDescription(self):
		return self.remotePortDescription
	def getRemoteSystemName(self):
		return self.remoteSystemName
	def getRemoteIpAddress(self):
		return self.remoteIpAddress

class OrionNodeMACAddresses():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.mAC=data['MAC']
		except:
			self.mAC=None
		try:
			self.dateTime=data['DateTime']
		except:
			self.dateTime=None

	def getNodeID(self):
		return self.nodeID
	def getMAC(self):
		return self.mAC
	def getDateTime(self):
		return self.dateTime

class OrionNodes():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.objectSubType=data['ObjectSubType']
		except:
			self.objectSubType=None
		try:
			self.iPAddress=data['IPAddress']
		except:
			self.iPAddress=None
		try:
			self.iPAddressType=data['IPAddressType']
		except:
			self.iPAddressType=None
		try:
			self.dynamicIP=data['DynamicIP']
		except:
			self.dynamicIP=None
		try:
			self.caption=data['Caption']
		except:
			self.caption=None
		try:
			self.nodeDescription=data['NodeDescription']
		except:
			self.nodeDescription=None
		try:
			self.dNS=data['DNS']
		except:
			self.dNS=None
		try:
			self.sysName=data['SysName']
		except:
			self.sysName=None
		try:
			self.vendor=data['Vendor']
		except:
			self.vendor=None
		try:
			self.sysObjectID=data['SysObjectID']
		except:
			self.sysObjectID=None
		try:
			self.location=data['Location']
		except:
			self.location=None
		try:
			self.contact=data['Contact']
		except:
			self.contact=None
		try:
			self.vendorIcon=data['VendorIcon']
		except:
			self.vendorIcon=None
		try:
			self.icon=data['Icon']
		except:
			self.icon=None
		try:
			self.iOSImage=data['IOSImage']
		except:
			self.iOSImage=None
		try:
			self.iOSVersion=data['IOSVersion']
		except:
			self.iOSVersion=None
		try:
			self.groupStatus=data['GroupStatus']
		except:
			self.groupStatus=None
		try:
			self.statusIcon=data['StatusIcon']
		except:
			self.statusIcon=None
		try:
			self.lastBoot=data['LastBoot']
		except:
			self.lastBoot=None
		try:
			self.systemUpTime=data['SystemUpTime']
		except:
			self.systemUpTime=None
		try:
			self.responseTime=data['ResponseTime']
		except:
			self.responseTime=None
		try:
			self.percentLoss=data['PercentLoss']
		except:
			self.percentLoss=None
		try:
			self.avgResponseTime=data['AvgResponseTime']
		except:
			self.avgResponseTime=None
		try:
			self.minResponseTime=data['MinResponseTime']
		except:
			self.minResponseTime=None
		try:
			self.maxResponseTime=data['MaxResponseTime']
		except:
			self.maxResponseTime=None
		try:
			self.cPULoad=data['CPULoad']
		except:
			self.cPULoad=None
		try:
			self.memoryUsed=data['MemoryUsed']
		except:
			self.memoryUsed=None
		try:
			self.percentMemoryUsed=data['PercentMemoryUsed']
		except:
			self.percentMemoryUsed=None
		try:
			self.lastSync=data['LastSync']
		except:
			self.lastSync=None
		try:
			self.lastSystemUpTimePollUtc=data['LastSystemUpTimePollUtc']
		except:
			self.lastSystemUpTimePollUtc=None
		try:
			self.machineType=data['MachineType']
		except:
			self.machineType=None
		try:
			self.severity=data['Severity']
		except:
			self.severity=None
		try:
			self.childStatus=data['ChildStatus']
		except:
			self.childStatus=None
		try:
			self.allow64BitCounters=data['Allow64BitCounters']
		except:
			self.allow64BitCounters=None
		try:
			self.agentPort=data['AgentPort']
		except:
			self.agentPort=None
		try:
			self.totalMemory=data['TotalMemory']
		except:
			self.totalMemory=None
		try:
			self.cMTS=data['CMTS']
		except:
			self.cMTS=None
		try:
			self.customPollerLastStatisticsPoll=data['CustomPollerLastStatisticsPoll']
		except:
			self.customPollerLastStatisticsPoll=None
		try:
			self.customPollerLastStatisticsPollSuccess=data['CustomPollerLastStatisticsPollSuccess']
		except:
			self.customPollerLastStatisticsPollSuccess=None
		try:
			self.sNMPVersion=data['SNMPVersion']
		except:
			self.sNMPVersion=None
		try:
			self.pollInterval=data['PollInterval']
		except:
			self.pollInterval=None
		try:
			self.engineID=data['EngineID']
		except:
			self.engineID=None
		try:
			self.rediscoveryInterval=data['RediscoveryInterval']
		except:
			self.rediscoveryInterval=None
		try:
			self.nextPoll=data['NextPoll']
		except:
			self.nextPoll=None
		try:
			self.nextRediscovery=data['NextRediscovery']
		except:
			self.nextRediscovery=None
		try:
			self.statCollection=data['StatCollection']
		except:
			self.statCollection=None
		try:
			self.external=data['External']
		except:
			self.external=None
		try:
			self.community=data['Community']
		except:
			self.community=None
		try:
			self.rWCommunity=data['RWCommunity']
		except:
			self.rWCommunity=None
		try:
			self.iP=data['IP']
		except:
			self.iP=None
		try:
			self.iP_Address=data['IP_Address']
		except:
			self.iP_Address=None
		try:
			self.iPAddressGUID=data['IPAddressGUID']
		except:
			self.iPAddressGUID=None
		try:
			self.nodeName=data['NodeName']
		except:
			self.nodeName=None
		try:
			self.blockUntil=data['BlockUntil']
		except:
			self.blockUntil=None
		try:
			self.bufferNoMemThisHour=data['BufferNoMemThisHour']
		except:
			self.bufferNoMemThisHour=None
		try:
			self.bufferNoMemToday=data['BufferNoMemToday']
		except:
			self.bufferNoMemToday=None
		try:
			self.bufferSmMissThisHour=data['BufferSmMissThisHour']
		except:
			self.bufferSmMissThisHour=None
		try:
			self.bufferSmMissToday=data['BufferSmMissToday']
		except:
			self.bufferSmMissToday=None
		try:
			self.bufferMdMissThisHour=data['BufferMdMissThisHour']
		except:
			self.bufferMdMissThisHour=None
		try:
			self.bufferMdMissToday=data['BufferMdMissToday']
		except:
			self.bufferMdMissToday=None
		try:
			self.bufferBgMissThisHour=data['BufferBgMissThisHour']
		except:
			self.bufferBgMissThisHour=None
		try:
			self.bufferBgMissToday=data['BufferBgMissToday']
		except:
			self.bufferBgMissToday=None
		try:
			self.bufferLgMissThisHour=data['BufferLgMissThisHour']
		except:
			self.bufferLgMissThisHour=None
		try:
			self.bufferLgMissToday=data['BufferLgMissToday']
		except:
			self.bufferLgMissToday=None
		try:
			self.bufferHgMissThisHour=data['BufferHgMissThisHour']
		except:
			self.bufferHgMissThisHour=None
		try:
			self.bufferHgMissToday=data['BufferHgMissToday']
		except:
			self.bufferHgMissToday=None
		try:
			self.orionIdPrefix=data['OrionIdPrefix']
		except:
			self.orionIdPrefix=None
		try:
			self.orionIdColumn=data['OrionIdColumn']
		except:
			self.orionIdColumn=None

	def getNodeID(self):
		return self.nodeID
	def getObjectSubType(self):
		return self.objectSubType
	def getIPAddress(self):
		return self.iPAddress
	def getIPAddressType(self):
		return self.iPAddressType
	def getDynamicIP(self):
		return self.dynamicIP
	def getCaption(self):
		return self.caption
	def getNodeDescription(self):
		return self.nodeDescription
	def getDNS(self):
		return self.dNS
	def getSysName(self):
		return self.sysName
	def getVendor(self):
		return self.vendor
	def getSysObjectID(self):
		return self.sysObjectID
	def getLocation(self):
		return self.location
	def getContact(self):
		return self.contact
	def getVendorIcon(self):
		return self.vendorIcon
	def getIcon(self):
		return self.icon
	def getIOSImage(self):
		return self.iOSImage
	def getIOSVersion(self):
		return self.iOSVersion
	def getGroupStatus(self):
		return self.groupStatus
	def getStatusIcon(self):
		return self.statusIcon
	def getLastBoot(self):
		return self.lastBoot
	def getSystemUpTime(self):
		return self.systemUpTime
	def getResponseTime(self):
		return self.responseTime
	def getPercentLoss(self):
		return self.percentLoss
	def getAvgResponseTime(self):
		return self.avgResponseTime
	def getMinResponseTime(self):
		return self.minResponseTime
	def getMaxResponseTime(self):
		return self.maxResponseTime
	def getCPULoad(self):
		return self.cPULoad
	def getMemoryUsed(self):
		return self.memoryUsed
	def getPercentMemoryUsed(self):
		return self.percentMemoryUsed
	def getLastSync(self):
		return self.lastSync
	def getLastSystemUpTimePollUtc(self):
		return self.lastSystemUpTimePollUtc
	def getMachineType(self):
		return self.machineType
	def getSeverity(self):
		return self.severity
	def getChildStatus(self):
		return self.childStatus
	def getAllow64BitCounters(self):
		return self.allow64BitCounters
	def getAgentPort(self):
		return self.agentPort
	def getTotalMemory(self):
		return self.totalMemory
	def getCMTS(self):
		return self.cMTS
	def getCustomPollerLastStatisticsPoll(self):
		return self.customPollerLastStatisticsPoll
	def getCustomPollerLastStatisticsPollSuccess(self):
		return self.customPollerLastStatisticsPollSuccess
	def getSNMPVersion(self):
		return self.sNMPVersion
	def getPollInterval(self):
		return self.pollInterval
	def getEngineID(self):
		return self.engineID
	def getRediscoveryInterval(self):
		return self.rediscoveryInterval
	def getNextPoll(self):
		return self.nextPoll
	def getNextRediscovery(self):
		return self.nextRediscovery
	def getStatCollection(self):
		return self.statCollection
	def getExternal(self):
		return self.external
	def getCommunity(self):
		return self.community
	def getRWCommunity(self):
		return self.rWCommunity
	def getIP(self):
		return self.iP
	def getIP_Address(self):
		return self.iP_Address
	def getIPAddressGUID(self):
		return self.iPAddressGUID
	def getNodeName(self):
		return self.nodeName
	def getBlockUntil(self):
		return self.blockUntil
	def getBufferNoMemThisHour(self):
		return self.bufferNoMemThisHour
	def getBufferNoMemToday(self):
		return self.bufferNoMemToday
	def getBufferSmMissThisHour(self):
		return self.bufferSmMissThisHour
	def getBufferSmMissToday(self):
		return self.bufferSmMissToday
	def getBufferMdMissThisHour(self):
		return self.bufferMdMissThisHour
	def getBufferMdMissToday(self):
		return self.bufferMdMissToday
	def getBufferBgMissThisHour(self):
		return self.bufferBgMissThisHour
	def getBufferBgMissToday(self):
		return self.bufferBgMissToday
	def getBufferLgMissThisHour(self):
		return self.bufferLgMissThisHour
	def getBufferLgMissToday(self):
		return self.bufferLgMissToday
	def getBufferHgMissThisHour(self):
		return self.bufferHgMissThisHour
	def getBufferHgMissToday(self):
		return self.bufferHgMissToday
	def getOrionIdPrefix(self):
		return self.orionIdPrefix
	def getOrionIdColumn(self):
		return self.orionIdColumn

class OrionNodesCustomProperties():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.city=data['City']
		except:
			self.city=None
		try:
			self.comments=data['Comments']
		except:
			self.comments=None
		try:
			self.department=data['Department']
		except:
			self.department=None

	def getNodeID(self):
		return self.nodeID
	def getCity(self):
		return self.city
	def getComments(self):
		return self.comments
	def getDepartment(self):
		return self.department

class OrionNodesStats():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.avgResponseTime=data['AvgResponseTime']
		except:
			self.avgResponseTime=None
		try:
			self.minResponseTime=data['MinResponseTime']
		except:
			self.minResponseTime=None
		try:
			self.maxResponseTime=data['MaxResponseTime']
		except:
			self.maxResponseTime=None
		try:
			self.responseTime=data['ResponseTime']
		except:
			self.responseTime=None
		try:
			self.percentLoss=data['PercentLoss']
		except:
			self.percentLoss=None
		try:
			self.cPULoad=data['CPULoad']
		except:
			self.cPULoad=None
		try:
			self.memoryUsed=data['MemoryUsed']
		except:
			self.memoryUsed=None
		try:
			self.percentMemoryUsed=data['PercentMemoryUsed']
		except:
			self.percentMemoryUsed=None
		try:
			self.lastBoot=data['LastBoot']
		except:
			self.lastBoot=None
		try:
			self.systemUpTime=data['SystemUpTime']
		except:
			self.systemUpTime=None
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None

	def getAvgResponseTime(self):
		return self.avgResponseTime
	def getMinResponseTime(self):
		return self.minResponseTime
	def getMaxResponseTime(self):
		return self.maxResponseTime
	def getResponseTime(self):
		return self.responseTime
	def getPercentLoss(self):
		return self.percentLoss
	def getCPULoad(self):
		return self.cPULoad
	def getMemoryUsed(self):
		return self.memoryUsed
	def getPercentMemoryUsed(self):
		return self.percentMemoryUsed
	def getLastBoot(self):
		return self.lastBoot
	def getSystemUpTime(self):
		return self.systemUpTime
	def getNodeID(self):
		return self.nodeID

class OrionNodeVlans():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.vlanId=data['VlanId']
		except:
			self.vlanId=None

	def getNodeID(self):
		return self.nodeID
	def getVlanId(self):
		return self.vlanId

class OrionNPMDiscoveredInterfaces():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.profileID=data['ProfileID']
		except:
			self.profileID=None
		try:
			self.discoveredNodeID=data['DiscoveredNodeID']
		except:
			self.discoveredNodeID=None
		try:
			self.discoveredInterfaceID=data['DiscoveredInterfaceID']
		except:
			self.discoveredInterfaceID=None
		try:
			self.interfaceIndex=data['InterfaceIndex']
		except:
			self.interfaceIndex=None
		try:
			self.interfaceName=data['InterfaceName']
		except:
			self.interfaceName=None
		try:
			self.interfaceType=data['InterfaceType']
		except:
			self.interfaceType=None
		try:
			self.interfaceSubType=data['InterfaceSubType']
		except:
			self.interfaceSubType=None
		try:
			self.interfaceTypeDescription=data['InterfaceTypeDescription']
		except:
			self.interfaceTypeDescription=None
		try:
			self.operStatus=data['OperStatus']
		except:
			self.operStatus=None
		try:
			self.adminStatus=data['AdminStatus']
		except:
			self.adminStatus=None
		try:
			self.physicalAddress=data['PhysicalAddress']
		except:
			self.physicalAddress=None
		try:
			self.ifName=data['IfName']
		except:
			self.ifName=None
		try:
			self.interfaceAlias=data['InterfaceAlias']
		except:
			self.interfaceAlias=None
		try:
			self.interfaceTypeName=data['InterfaceTypeName']
		except:
			self.interfaceTypeName=None
		try:
			self.ignoredInterfaceID=data['IgnoredInterfaceID']
		except:
			self.ignoredInterfaceID=None

	def getProfileID(self):
		return self.profileID
	def getDiscoveredNodeID(self):
		return self.discoveredNodeID
	def getDiscoveredInterfaceID(self):
		return self.discoveredInterfaceID
	def getInterfaceIndex(self):
		return self.interfaceIndex
	def getInterfaceName(self):
		return self.interfaceName
	def getInterfaceType(self):
		return self.interfaceType
	def getInterfaceSubType(self):
		return self.interfaceSubType
	def getInterfaceTypeDescription(self):
		return self.interfaceTypeDescription
	def getOperStatus(self):
		return self.operStatus
	def getAdminStatus(self):
		return self.adminStatus
	def getPhysicalAddress(self):
		return self.physicalAddress
	def getIfName(self):
		return self.ifName
	def getInterfaceAlias(self):
		return self.interfaceAlias
	def getInterfaceTypeName(self):
		return self.interfaceTypeName
	def getIgnoredInterfaceID(self):
		return self.ignoredInterfaceID

class OrionNPMInterfaceAvailability():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.dateTime=data['DateTime']
		except:
			self.dateTime=None
		try:
			self.interfaceID=data['InterfaceID']
		except:
			self.interfaceID=None
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.availability=data['Availability']
		except:
			self.availability=None
		try:
			self.weight=data['Weight']
		except:
			self.weight=None

	def getDateTime(self):
		return self.dateTime
	def getInterfaceID(self):
		return self.interfaceID
	def getNodeID(self):
		return self.nodeID
	def getAvailability(self):
		return self.availability
	def getWeight(self):
		return self.weight

class OrionNPMInterfaceErrors():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.interfaceID=data['InterfaceID']
		except:
			self.interfaceID=None
		try:
			self.dateTime=data['DateTime']
		except:
			self.dateTime=None
		try:
			self.archive=data['Archive']
		except:
			self.archive=None
		try:
			self.inErrors=data['InErrors']
		except:
			self.inErrors=None
		try:
			self.inDiscards=data['InDiscards']
		except:
			self.inDiscards=None
		try:
			self.outErrors=data['OutErrors']
		except:
			self.outErrors=None
		try:
			self.outDiscards=data['OutDiscards']
		except:
			self.outDiscards=None

	def getNodeID(self):
		return self.nodeID
	def getInterfaceID(self):
		return self.interfaceID
	def getDateTime(self):
		return self.dateTime
	def getArchive(self):
		return self.archive
	def getInErrors(self):
		return self.inErrors
	def getInDiscards(self):
		return self.inDiscards
	def getOutErrors(self):
		return self.outErrors
	def getOutDiscards(self):
		return self.outDiscards

class OrionNPMInterfaces():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.interfaceID=data['InterfaceID']
		except:
			self.interfaceID=None
		try:
			self.objectSubType=data['ObjectSubType']
		except:
			self.objectSubType=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.index=data['Index']
		except:
			self.index=None
		try:
			self.icon=data['Icon']
		except:
			self.icon=None
		try:
			self.type=data['Type']
		except:
			self.type=None
		try:
			self.typeName=data['TypeName']
		except:
			self.typeName=None
		try:
			self.typeDescription=data['TypeDescription']
		except:
			self.typeDescription=None
		try:
			self.speed=data['Speed']
		except:
			self.speed=None
		try:
			self.mTU=data['MTU']
		except:
			self.mTU=None
		try:
			self.lastChange=data['LastChange']
		except:
			self.lastChange=None
		try:
			self.physicalAddress=data['PhysicalAddress']
		except:
			self.physicalAddress=None
		try:
			self.adminStatus=data['AdminStatus']
		except:
			self.adminStatus=None
		try:
			self.operStatus=data['OperStatus']
		except:
			self.operStatus=None
		try:
			self.statusIcon=data['StatusIcon']
		except:
			self.statusIcon=None
		try:
			self.inBandwidth=data['InBandwidth']
		except:
			self.inBandwidth=None
		try:
			self.outBandwidth=data['OutBandwidth']
		except:
			self.outBandwidth=None
		try:
			self.caption=data['Caption']
		except:
			self.caption=None
		try:
			self.fullName=data['FullName']
		except:
			self.fullName=None
		try:
			self.outbps=data['Outbps']
		except:
			self.outbps=None
		try:
			self.inbps=data['Inbps']
		except:
			self.inbps=None
		try:
			self.outPercentUtil=data['OutPercentUtil']
		except:
			self.outPercentUtil=None
		try:
			self.inPercentUtil=data['InPercentUtil']
		except:
			self.inPercentUtil=None
		try:
			self.outPps=data['OutPps']
		except:
			self.outPps=None
		try:
			self.inPps=data['InPps']
		except:
			self.inPps=None
		try:
			self.inPktSize=data['InPktSize']
		except:
			self.inPktSize=None
		try:
			self.outPktSize=data['OutPktSize']
		except:
			self.outPktSize=None
		try:
			self.outUcastPps=data['OutUcastPps']
		except:
			self.outUcastPps=None
		try:
			self.outMcastPps=data['OutMcastPps']
		except:
			self.outMcastPps=None
		try:
			self.inUcastPps=data['InUcastPps']
		except:
			self.inUcastPps=None
		try:
			self.inMcastPps=data['InMcastPps']
		except:
			self.inMcastPps=None
		try:
			self.inDiscardsThisHour=data['InDiscardsThisHour']
		except:
			self.inDiscardsThisHour=None
		try:
			self.inDiscardsToday=data['InDiscardsToday']
		except:
			self.inDiscardsToday=None
		try:
			self.inErrorsThisHour=data['InErrorsThisHour']
		except:
			self.inErrorsThisHour=None
		try:
			self.inErrorsToday=data['InErrorsToday']
		except:
			self.inErrorsToday=None
		try:
			self.outDiscardsThisHour=data['OutDiscardsThisHour']
		except:
			self.outDiscardsThisHour=None
		try:
			self.outDiscardsToday=data['OutDiscardsToday']
		except:
			self.outDiscardsToday=None
		try:
			self.outErrorsThisHour=data['OutErrorsThisHour']
		except:
			self.outErrorsThisHour=None
		try:
			self.outErrorsToday=data['OutErrorsToday']
		except:
			self.outErrorsToday=None
		try:
			self.maxInBpsToday=data['MaxInBpsToday']
		except:
			self.maxInBpsToday=None
		try:
			self.maxInBpsTime=data['MaxInBpsTime']
		except:
			self.maxInBpsTime=None
		try:
			self.maxOutBpsToday=data['MaxOutBpsToday']
		except:
			self.maxOutBpsToday=None
		try:
			self.maxOutBpsTime=data['MaxOutBpsTime']
		except:
			self.maxOutBpsTime=None
		try:
			self.counter64=data['Counter64']
		except:
			self.counter64=None
		try:
			self.lastSync=data['LastSync']
		except:
			self.lastSync=None
		try:
			self.alias=data['Alias']
		except:
			self.alias=None
		try:
			self.ifName=data['IfName']
		except:
			self.ifName=None
		try:
			self.severity=data['Severity']
		except:
			self.severity=None
		try:
			self.customBandwidth=data['CustomBandwidth']
		except:
			self.customBandwidth=None
		try:
			self.customPollerLastStatisticsPoll=data['CustomPollerLastStatisticsPoll']
		except:
			self.customPollerLastStatisticsPoll=None
		try:
			self.pollInterval=data['PollInterval']
		except:
			self.pollInterval=None
		try:
			self.nextPoll=data['NextPoll']
		except:
			self.nextPoll=None
		try:
			self.rediscoveryInterval=data['RediscoveryInterval']
		except:
			self.rediscoveryInterval=None
		try:
			self.nextRediscovery=data['NextRediscovery']
		except:
			self.nextRediscovery=None
		try:
			self.statCollection=data['StatCollection']
		except:
			self.statCollection=None
		try:
			self.unPluggable=data['UnPluggable']
		except:
			self.unPluggable=None
		try:
			self.interfaceSpeed=data['InterfaceSpeed']
		except:
			self.interfaceSpeed=None
		try:
			self.interfaceCaption=data['InterfaceCaption']
		except:
			self.interfaceCaption=None
		try:
			self.interfaceType=data['InterfaceType']
		except:
			self.interfaceType=None
		try:
			self.interfaceSubType=data['InterfaceSubType']
		except:
			self.interfaceSubType=None
		try:
			self.mAC=data['MAC']
		except:
			self.mAC=None
		try:
			self.interfaceName=data['InterfaceName']
		except:
			self.interfaceName=None
		try:
			self.interfaceIcon=data['InterfaceIcon']
		except:
			self.interfaceIcon=None
		try:
			self.interfaceTypeName=data['InterfaceTypeName']
		except:
			self.interfaceTypeName=None
		try:
			self.adminStatusLED=data['AdminStatusLED']
		except:
			self.adminStatusLED=None
		try:
			self.operStatusLED=data['OperStatusLED']
		except:
			self.operStatusLED=None
		try:
			self.interfaceAlias=data['InterfaceAlias']
		except:
			self.interfaceAlias=None
		try:
			self.interfaceIndex=data['InterfaceIndex']
		except:
			self.interfaceIndex=None
		try:
			self.interfaceLastChange=data['InterfaceLastChange']
		except:
			self.interfaceLastChange=None
		try:
			self.interfaceMTU=data['InterfaceMTU']
		except:
			self.interfaceMTU=None
		try:
			self.interfaceTypeDescription=data['InterfaceTypeDescription']
		except:
			self.interfaceTypeDescription=None
		try:
			self.orionIdPrefix=data['OrionIdPrefix']
		except:
			self.orionIdPrefix=None
		try:
			self.orionIdColumn=data['OrionIdColumn']
		except:
			self.orionIdColumn=None

	def getNodeID(self):
		return self.nodeID
	def getInterfaceID(self):
		return self.interfaceID
	def getObjectSubType(self):
		return self.objectSubType
	def getName(self):
		return self.name
	def getIndex(self):
		return self.index
	def getIcon(self):
		return self.icon
	def getType(self):
		return self.type
	def getTypeName(self):
		return self.typeName
	def getTypeDescription(self):
		return self.typeDescription
	def getSpeed(self):
		return self.speed
	def getMTU(self):
		return self.mTU
	def getLastChange(self):
		return self.lastChange
	def getPhysicalAddress(self):
		return self.physicalAddress
	def getAdminStatus(self):
		return self.adminStatus
	def getOperStatus(self):
		return self.operStatus
	def getStatusIcon(self):
		return self.statusIcon
	def getInBandwidth(self):
		return self.inBandwidth
	def getOutBandwidth(self):
		return self.outBandwidth
	def getCaption(self):
		return self.caption
	def getFullName(self):
		return self.fullName
	def getOutbps(self):
		return self.outbps
	def getInbps(self):
		return self.inbps
	def getOutPercentUtil(self):
		return self.outPercentUtil
	def getInPercentUtil(self):
		return self.inPercentUtil
	def getOutPps(self):
		return self.outPps
	def getInPps(self):
		return self.inPps
	def getInPktSize(self):
		return self.inPktSize
	def getOutPktSize(self):
		return self.outPktSize
	def getOutUcastPps(self):
		return self.outUcastPps
	def getOutMcastPps(self):
		return self.outMcastPps
	def getInUcastPps(self):
		return self.inUcastPps
	def getInMcastPps(self):
		return self.inMcastPps
	def getInDiscardsThisHour(self):
		return self.inDiscardsThisHour
	def getInDiscardsToday(self):
		return self.inDiscardsToday
	def getInErrorsThisHour(self):
		return self.inErrorsThisHour
	def getInErrorsToday(self):
		return self.inErrorsToday
	def getOutDiscardsThisHour(self):
		return self.outDiscardsThisHour
	def getOutDiscardsToday(self):
		return self.outDiscardsToday
	def getOutErrorsThisHour(self):
		return self.outErrorsThisHour
	def getOutErrorsToday(self):
		return self.outErrorsToday
	def getMaxInBpsToday(self):
		return self.maxInBpsToday
	def getMaxInBpsTime(self):
		return self.maxInBpsTime
	def getMaxOutBpsToday(self):
		return self.maxOutBpsToday
	def getMaxOutBpsTime(self):
		return self.maxOutBpsTime
	def getCounter64(self):
		return self.counter64
	def getLastSync(self):
		return self.lastSync
	def getAlias(self):
		return self.alias
	def getIfName(self):
		return self.ifName
	def getSeverity(self):
		return self.severity
	def getCustomBandwidth(self):
		return self.customBandwidth
	def getCustomPollerLastStatisticsPoll(self):
		return self.customPollerLastStatisticsPoll
	def getPollInterval(self):
		return self.pollInterval
	def getNextPoll(self):
		return self.nextPoll
	def getRediscoveryInterval(self):
		return self.rediscoveryInterval
	def getNextRediscovery(self):
		return self.nextRediscovery
	def getStatCollection(self):
		return self.statCollection
	def getUnPluggable(self):
		return self.unPluggable
	def getInterfaceSpeed(self):
		return self.interfaceSpeed
	def getInterfaceCaption(self):
		return self.interfaceCaption
	def getInterfaceType(self):
		return self.interfaceType
	def getInterfaceSubType(self):
		return self.interfaceSubType
	def getMAC(self):
		return self.mAC
	def getInterfaceName(self):
		return self.interfaceName
	def getInterfaceIcon(self):
		return self.interfaceIcon
	def getInterfaceTypeName(self):
		return self.interfaceTypeName
	def getAdminStatusLED(self):
		return self.adminStatusLED
	def getOperStatusLED(self):
		return self.operStatusLED
	def getInterfaceAlias(self):
		return self.interfaceAlias
	def getInterfaceIndex(self):
		return self.interfaceIndex
	def getInterfaceLastChange(self):
		return self.interfaceLastChange
	def getInterfaceMTU(self):
		return self.interfaceMTU
	def getInterfaceTypeDescription(self):
		return self.interfaceTypeDescription
	def getOrionIdPrefix(self):
		return self.orionIdPrefix
	def getOrionIdColumn(self):
		return self.orionIdColumn

class OrionNPMInterfaceTraffic():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.interfaceID=data['InterfaceID']
		except:
			self.interfaceID=None
		try:
			self.dateTime=data['DateTime']
		except:
			self.dateTime=None
		try:
			self.archive=data['Archive']
		except:
			self.archive=None
		try:
			self.inAveragebps=data['InAveragebps']
		except:
			self.inAveragebps=None
		try:
			self.inMinbps=data['InMinbps']
		except:
			self.inMinbps=None
		try:
			self.inMaxbps=data['InMaxbps']
		except:
			self.inMaxbps=None
		try:
			self.inTotalBytes=data['InTotalBytes']
		except:
			self.inTotalBytes=None
		try:
			self.inTotalPkts=data['InTotalPkts']
		except:
			self.inTotalPkts=None
		try:
			self.inAvgUniCastPkts=data['InAvgUniCastPkts']
		except:
			self.inAvgUniCastPkts=None
		try:
			self.inMinUniCastPkts=data['InMinUniCastPkts']
		except:
			self.inMinUniCastPkts=None
		try:
			self.inMaxUniCastPkts=data['InMaxUniCastPkts']
		except:
			self.inMaxUniCastPkts=None
		try:
			self.inAvgMultiCastPkts=data['InAvgMultiCastPkts']
		except:
			self.inAvgMultiCastPkts=None
		try:
			self.inMinMultiCastPkts=data['InMinMultiCastPkts']
		except:
			self.inMinMultiCastPkts=None
		try:
			self.inMaxMultiCastPkts=data['InMaxMultiCastPkts']
		except:
			self.inMaxMultiCastPkts=None
		try:
			self.outAveragebps=data['OutAveragebps']
		except:
			self.outAveragebps=None
		try:
			self.outMinbps=data['OutMinbps']
		except:
			self.outMinbps=None
		try:
			self.outMaxbps=data['OutMaxbps']
		except:
			self.outMaxbps=None
		try:
			self.outTotalBytes=data['OutTotalBytes']
		except:
			self.outTotalBytes=None
		try:
			self.outTotalPkts=data['OutTotalPkts']
		except:
			self.outTotalPkts=None
		try:
			self.outAvgUniCastPkts=data['OutAvgUniCastPkts']
		except:
			self.outAvgUniCastPkts=None
		try:
			self.outMaxUniCastPkts=data['OutMaxUniCastPkts']
		except:
			self.outMaxUniCastPkts=None
		try:
			self.outMinUniCastPkts=data['OutMinUniCastPkts']
		except:
			self.outMinUniCastPkts=None
		try:
			self.outAvgMultiCastPkts=data['OutAvgMultiCastPkts']
		except:
			self.outAvgMultiCastPkts=None
		try:
			self.outMinMultiCastPkts=data['OutMinMultiCastPkts']
		except:
			self.outMinMultiCastPkts=None
		try:
			self.outMaxMultiCastPkts=data['OutMaxMultiCastPkts']
		except:
			self.outMaxMultiCastPkts=None

	def getNodeID(self):
		return self.nodeID
	def getInterfaceID(self):
		return self.interfaceID
	def getDateTime(self):
		return self.dateTime
	def getArchive(self):
		return self.archive
	def getInAveragebps(self):
		return self.inAveragebps
	def getInMinbps(self):
		return self.inMinbps
	def getInMaxbps(self):
		return self.inMaxbps
	def getInTotalBytes(self):
		return self.inTotalBytes
	def getInTotalPkts(self):
		return self.inTotalPkts
	def getInAvgUniCastPkts(self):
		return self.inAvgUniCastPkts
	def getInMinUniCastPkts(self):
		return self.inMinUniCastPkts
	def getInMaxUniCastPkts(self):
		return self.inMaxUniCastPkts
	def getInAvgMultiCastPkts(self):
		return self.inAvgMultiCastPkts
	def getInMinMultiCastPkts(self):
		return self.inMinMultiCastPkts
	def getInMaxMultiCastPkts(self):
		return self.inMaxMultiCastPkts
	def getOutAveragebps(self):
		return self.outAveragebps
	def getOutMinbps(self):
		return self.outMinbps
	def getOutMaxbps(self):
		return self.outMaxbps
	def getOutTotalBytes(self):
		return self.outTotalBytes
	def getOutTotalPkts(self):
		return self.outTotalPkts
	def getOutAvgUniCastPkts(self):
		return self.outAvgUniCastPkts
	def getOutMaxUniCastPkts(self):
		return self.outMaxUniCastPkts
	def getOutMinUniCastPkts(self):
		return self.outMinUniCastPkts
	def getOutAvgMultiCastPkts(self):
		return self.outAvgMultiCastPkts
	def getOutMinMultiCastPkts(self):
		return self.outMinMultiCastPkts
	def getOutMaxMultiCastPkts(self):
		return self.outMaxMultiCastPkts

class OrionPollers():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.pollerID=data['PollerID']
		except:
			self.pollerID=None
		try:
			self.pollerType=data['PollerType']
		except:
			self.pollerType=None
		try:
			self.netObject=data['NetObject']
		except:
			self.netObject=None
		try:
			self.netObjectType=data['NetObjectType']
		except:
			self.netObjectType=None
		try:
			self.netObjectID=data['NetObjectID']
		except:
			self.netObjectID=None
		try:
			self.enabled=data['Enabled']
		except:
			self.enabled=None

	def getPollerID(self):
		return self.pollerID
	def getPollerType(self):
		return self.pollerType
	def getNetObject(self):
		return self.netObject
	def getNetObjectType(self):
		return self.netObjectType
	def getNetObjectID(self):
		return self.netObjectID
	def getEnabled(self):
		return self.enabled

class OrionReport():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.reportID=data['ReportID']
		except:
			self.reportID=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.category=data['Category']
		except:
			self.category=None
		try:
			self.title=data['Title']
		except:
			self.title=None
		try:
			self.type=data['Type']
		except:
			self.type=None
		try:
			self.subTitle=data['SubTitle']
		except:
			self.subTitle=None
		try:
			self.description=data['Description']
		except:
			self.description=None
		try:
			self.legacyPath=data['LegacyPath']
		except:
			self.legacyPath=None
		try:
			self.definition=data['Definition']
		except:
			self.definition=None
		try:
			self.moduleTitle=data['ModuleTitle']
		except:
			self.moduleTitle=None
		try:
			self.recipientList=data['RecipientList']
		except:
			self.recipientList=None
		try:
			self.limitationCategory=data['LimitationCategory']
		except:
			self.limitationCategory=None
		try:
			self.owner=data['Owner']
		except:
			self.owner=None
		try:
			self.lastRenderDuration=data['LastRenderDuration']
		except:
			self.lastRenderDuration=None

	def getReportID(self):
		return self.reportID
	def getName(self):
		return self.name
	def getCategory(self):
		return self.category
	def getTitle(self):
		return self.title
	def getType(self):
		return self.type
	def getSubTitle(self):
		return self.subTitle
	def getDescription(self):
		return self.description
	def getLegacyPath(self):
		return self.legacyPath
	def getDefinition(self):
		return self.definition
	def getModuleTitle(self):
		return self.moduleTitle
	def getRecipientList(self):
		return self.recipientList
	def getLimitationCategory(self):
		return self.limitationCategory
	def getOwner(self):
		return self.owner
	def getLastRenderDuration(self):
		return self.lastRenderDuration

class OrionResponseTime():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.dateTime=data['DateTime']
		except:
			self.dateTime=None
		try:
			self.archive=data['Archive']
		except:
			self.archive=None
		try:
			self.avgResponseTime=data['AvgResponseTime']
		except:
			self.avgResponseTime=None
		try:
			self.minResponseTime=data['MinResponseTime']
		except:
			self.minResponseTime=None
		try:
			self.maxResponseTime=data['MaxResponseTime']
		except:
			self.maxResponseTime=None
		try:
			self.percentLoss=data['PercentLoss']
		except:
			self.percentLoss=None
		try:
			self.availability=data['Availability']
		except:
			self.availability=None

	def getNodeID(self):
		return self.nodeID
	def getDateTime(self):
		return self.dateTime
	def getArchive(self):
		return self.archive
	def getAvgResponseTime(self):
		return self.avgResponseTime
	def getMinResponseTime(self):
		return self.minResponseTime
	def getMaxResponseTime(self):
		return self.maxResponseTime
	def getPercentLoss(self):
		return self.percentLoss
	def getAvailability(self):
		return self.availability

class OrionServices():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.displayName=data['DisplayName']
		except:
			self.displayName=None
		try:
			self.serviceName=data['ServiceName']
		except:
			self.serviceName=None
		try:
			self.status=data['Status']
		except:
			self.status=None
		try:
			self.memory=data['Memory']
		except:
			self.memory=None

	def getDisplayName(self):
		return self.displayName
	def getServiceName(self):
		return self.serviceName
	def getStatus(self):
		return self.status
	def getMemory(self):
		return self.memory

class OrionSysLog():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.messageID=data['MessageID']
		except:
			self.messageID=None
		try:
			self.engineID=data['EngineID']
		except:
			self.engineID=None
		try:
			self.dateTime=data['DateTime']
		except:
			self.dateTime=None
		try:
			self.iPAddress=data['IPAddress']
		except:
			self.iPAddress=None
		try:
			self.acknowledged=data['Acknowledged']
		except:
			self.acknowledged=None
		try:
			self.sysLogFacility=data['SysLogFacility']
		except:
			self.sysLogFacility=None
		try:
			self.sysLogSeverity=data['SysLogSeverity']
		except:
			self.sysLogSeverity=None
		try:
			self.hostname=data['Hostname']
		except:
			self.hostname=None
		try:
			self.messageType=data['MessageType']
		except:
			self.messageType=None
		try:
			self.message=data['Message']
		except:
			self.message=None
		try:
			self.sysLogTag=data['SysLogTag']
		except:
			self.sysLogTag=None
		try:
			self.firstIPInMessage=data['FirstIPInMessage']
		except:
			self.firstIPInMessage=None
		try:
			self.secIPInMessage=data['SecIPInMessage']
		except:
			self.secIPInMessage=None
		try:
			self.macInMessage=data['MacInMessage']
		except:
			self.macInMessage=None
		try:
			self.timeStamp=data['TimeStamp']
		except:
			self.timeStamp=None
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None

	def getMessageID(self):
		return self.messageID
	def getEngineID(self):
		return self.engineID
	def getDateTime(self):
		return self.dateTime
	def getIPAddress(self):
		return self.iPAddress
	def getAcknowledged(self):
		return self.acknowledged
	def getSysLogFacility(self):
		return self.sysLogFacility
	def getSysLogSeverity(self):
		return self.sysLogSeverity
	def getHostname(self):
		return self.hostname
	def getMessageType(self):
		return self.messageType
	def getMessage(self):
		return self.message
	def getSysLogTag(self):
		return self.sysLogTag
	def getFirstIPInMessage(self):
		return self.firstIPInMessage
	def getSecIPInMessage(self):
		return self.secIPInMessage
	def getMacInMessage(self):
		return self.macInMessage
	def getTimeStamp(self):
		return self.timeStamp
	def getNodeID(self):
		return self.nodeID

class OrionTopologyData():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.discoveryProfileID=data['DiscoveryProfileID']
		except:
			self.discoveryProfileID=None
		try:
			self.srcNodeID=data['SrcNodeID']
		except:
			self.srcNodeID=None
		try:
			self.srcInterfaceID=data['SrcInterfaceID']
		except:
			self.srcInterfaceID=None
		try:
			self.destNodeID=data['DestNodeID']
		except:
			self.destNodeID=None
		try:
			self.destInterfaceID=data['DestInterfaceID']
		except:
			self.destInterfaceID=None
		try:
			self.srcType=data['SrcType']
		except:
			self.srcType=None
		try:
			self.destType=data['DestType']
		except:
			self.destType=None
		try:
			self.dataSourceNodeID=data['DataSourceNodeID']
		except:
			self.dataSourceNodeID=None
		try:
			self.lastUpdateUtc=data['LastUpdateUtc']
		except:
			self.lastUpdateUtc=None

	def getDiscoveryProfileID(self):
		return self.discoveryProfileID
	def getSrcNodeID(self):
		return self.srcNodeID
	def getSrcInterfaceID(self):
		return self.srcInterfaceID
	def getDestNodeID(self):
		return self.destNodeID
	def getDestInterfaceID(self):
		return self.destInterfaceID
	def getSrcType(self):
		return self.srcType
	def getDestType(self):
		return self.destType
	def getDataSourceNodeID(self):
		return self.dataSourceNodeID
	def getLastUpdateUtc(self):
		return self.lastUpdateUtc

class OrionTraps():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.trapID=data['TrapID']
		except:
			self.trapID=None
		try:
			self.engineID=data['EngineID']
		except:
			self.engineID=None
		try:
			self.dateTime=data['DateTime']
		except:
			self.dateTime=None
		try:
			self.iPAddress=data['IPAddress']
		except:
			self.iPAddress=None
		try:
			self.community=data['Community']
		except:
			self.community=None
		try:
			self.tag=data['Tag']
		except:
			self.tag=None
		try:
			self.acknowledged=data['Acknowledged']
		except:
			self.acknowledged=None
		try:
			self.hostname=data['Hostname']
		except:
			self.hostname=None
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.trapType=data['TrapType']
		except:
			self.trapType=None
		try:
			self.colorCode=data['ColorCode']
		except:
			self.colorCode=None
		try:
			self.timeStamp=data['TimeStamp']
		except:
			self.timeStamp=None

	def getTrapID(self):
		return self.trapID
	def getEngineID(self):
		return self.engineID
	def getDateTime(self):
		return self.dateTime
	def getIPAddress(self):
		return self.iPAddress
	def getCommunity(self):
		return self.community
	def getTag(self):
		return self.tag
	def getAcknowledged(self):
		return self.acknowledged
	def getHostname(self):
		return self.hostname
	def getNodeID(self):
		return self.nodeID
	def getTrapType(self):
		return self.trapType
	def getColorCode(self):
		return self.colorCode
	def getTimeStamp(self):
		return self.timeStamp

class OrionViews():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.viewID=data['ViewID']
		except:
			self.viewID=None
		try:
			self.viewKey=data['ViewKey']
		except:
			self.viewKey=None
		try:
			self.viewTitle=data['ViewTitle']
		except:
			self.viewTitle=None
		try:
			self.viewType=data['ViewType']
		except:
			self.viewType=None
		try:
			self.columns=data['Columns']
		except:
			self.columns=None
		try:
			self.column1Width=data['Column1Width']
		except:
			self.column1Width=None
		try:
			self.column2Width=data['Column2Width']
		except:
			self.column2Width=None
		try:
			self.column3Width=data['Column3Width']
		except:
			self.column3Width=None
		try:
			self.system=data['System']
		except:
			self.system=None
		try:
			self.customizable=data['Customizable']
		except:
			self.customizable=None
		try:
			self.limitationID=data['LimitationID']
		except:
			self.limitationID=None

	def getViewID(self):
		return self.viewID
	def getViewKey(self):
		return self.viewKey
	def getViewTitle(self):
		return self.viewTitle
	def getViewType(self):
		return self.viewType
	def getColumns(self):
		return self.columns
	def getColumn1Width(self):
		return self.column1Width
	def getColumn2Width(self):
		return self.column2Width
	def getColumn3Width(self):
		return self.column3Width
	def getSystem(self):
		return self.system
	def getCustomizable(self):
		return self.customizable
	def getLimitationID(self):
		return self.limitationID

class OrionVIMClusters():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.clusterID=data['ClusterID']
		except:
			self.clusterID=None
		try:
			self.managedObjectID=data['ManagedObjectID']
		except:
			self.managedObjectID=None
		try:
			self.dataCenterID=data['DataCenterID']
		except:
			self.dataCenterID=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.totalMemory=data['TotalMemory']
		except:
			self.totalMemory=None
		try:
			self.totalCpu=data['TotalCpu']
		except:
			self.totalCpu=None
		try:
			self.cpuCoreCount=data['CpuCoreCount']
		except:
			self.cpuCoreCount=None
		try:
			self.cpuThreadCount=data['CpuThreadCount']
		except:
			self.cpuThreadCount=None
		try:
			self.effectiveCpu=data['EffectiveCpu']
		except:
			self.effectiveCpu=None
		try:
			self.effectiveMemory=data['EffectiveMemory']
		except:
			self.effectiveMemory=None
		try:
			self.drsBehaviour=data['DrsBehaviour']
		except:
			self.drsBehaviour=None
		try:
			self.drsStatus=data['DrsStatus']
		except:
			self.drsStatus=None
		try:
			self.drsVmotionRate=data['DrsVmotionRate']
		except:
			self.drsVmotionRate=None
		try:
			self.haAdmissionControlStatus=data['HaAdmissionControlStatus']
		except:
			self.haAdmissionControlStatus=None
		try:
			self.haStatus=data['HaStatus']
		except:
			self.haStatus=None
		try:
			self.haFailoverLevel=data['HaFailoverLevel']
		except:
			self.haFailoverLevel=None
		try:
			self.configStatus=data['ConfigStatus']
		except:
			self.configStatus=None
		try:
			self.overallStatus=data['OverallStatus']
		except:
			self.overallStatus=None
		try:
			self.cPULoad=data['CPULoad']
		except:
			self.cPULoad=None
		try:
			self.cPUUsageMHz=data['CPUUsageMHz']
		except:
			self.cPUUsageMHz=None
		try:
			self.memoryUsage=data['MemoryUsage']
		except:
			self.memoryUsage=None
		try:
			self.memoryUsageMB=data['MemoryUsageMB']
		except:
			self.memoryUsageMB=None

	def getClusterID(self):
		return self.clusterID
	def getManagedObjectID(self):
		return self.managedObjectID
	def getDataCenterID(self):
		return self.dataCenterID
	def getName(self):
		return self.name
	def getTotalMemory(self):
		return self.totalMemory
	def getTotalCpu(self):
		return self.totalCpu
	def getCpuCoreCount(self):
		return self.cpuCoreCount
	def getCpuThreadCount(self):
		return self.cpuThreadCount
	def getEffectiveCpu(self):
		return self.effectiveCpu
	def getEffectiveMemory(self):
		return self.effectiveMemory
	def getDrsBehaviour(self):
		return self.drsBehaviour
	def getDrsStatus(self):
		return self.drsStatus
	def getDrsVmotionRate(self):
		return self.drsVmotionRate
	def getHaAdmissionControlStatus(self):
		return self.haAdmissionControlStatus
	def getHaStatus(self):
		return self.haStatus
	def getHaFailoverLevel(self):
		return self.haFailoverLevel
	def getConfigStatus(self):
		return self.configStatus
	def getOverallStatus(self):
		return self.overallStatus
	def getCPULoad(self):
		return self.cPULoad
	def getCPUUsageMHz(self):
		return self.cPUUsageMHz
	def getMemoryUsage(self):
		return self.memoryUsage
	def getMemoryUsageMB(self):
		return self.memoryUsageMB

class OrionVIMClusterStatistics():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.clusterID=data['ClusterID']
		except:
			self.clusterID=None
		try:
			self.dateTime=data['DateTime']
		except:
			self.dateTime=None
		try:
			self.percentAvailability=data['PercentAvailability']
		except:
			self.percentAvailability=None
		try:
			self.minCPULoad=data['MinCPULoad']
		except:
			self.minCPULoad=None
		try:
			self.maxCPULoad=data['MaxCPULoad']
		except:
			self.maxCPULoad=None
		try:
			self.avgCPULoad=data['AvgCPULoad']
		except:
			self.avgCPULoad=None
		try:
			self.minCPUUsageMHz=data['MinCPUUsageMHz']
		except:
			self.minCPUUsageMHz=None
		try:
			self.maxCPUUsageMHz=data['MaxCPUUsageMHz']
		except:
			self.maxCPUUsageMHz=None
		try:
			self.avgCPUUsageMHz=data['AvgCPUUsageMHz']
		except:
			self.avgCPUUsageMHz=None
		try:
			self.minMemoryUsage=data['MinMemoryUsage']
		except:
			self.minMemoryUsage=None
		try:
			self.maxMemoryUsage=data['MaxMemoryUsage']
		except:
			self.maxMemoryUsage=None
		try:
			self.avgMemoryUsage=data['AvgMemoryUsage']
		except:
			self.avgMemoryUsage=None
		try:
			self.minMemoryUsageMB=data['MinMemoryUsageMB']
		except:
			self.minMemoryUsageMB=None
		try:
			self.maxMemoryUsageMB=data['MaxMemoryUsageMB']
		except:
			self.maxMemoryUsageMB=None
		try:
			self.avgMemoryUsageMB=data['AvgMemoryUsageMB']
		except:
			self.avgMemoryUsageMB=None

	def getClusterID(self):
		return self.clusterID
	def getDateTime(self):
		return self.dateTime
	def getPercentAvailability(self):
		return self.percentAvailability
	def getMinCPULoad(self):
		return self.minCPULoad
	def getMaxCPULoad(self):
		return self.maxCPULoad
	def getAvgCPULoad(self):
		return self.avgCPULoad
	def getMinCPUUsageMHz(self):
		return self.minCPUUsageMHz
	def getMaxCPUUsageMHz(self):
		return self.maxCPUUsageMHz
	def getAvgCPUUsageMHz(self):
		return self.avgCPUUsageMHz
	def getMinMemoryUsage(self):
		return self.minMemoryUsage
	def getMaxMemoryUsage(self):
		return self.maxMemoryUsage
	def getAvgMemoryUsage(self):
		return self.avgMemoryUsage
	def getMinMemoryUsageMB(self):
		return self.minMemoryUsageMB
	def getMaxMemoryUsageMB(self):
		return self.maxMemoryUsageMB
	def getAvgMemoryUsageMB(self):
		return self.avgMemoryUsageMB

class OrionVIMDataCenters():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.dataCenterID=data['DataCenterID']
		except:
			self.dataCenterID=None
		try:
			self.managedObjectID=data['ManagedObjectID']
		except:
			self.managedObjectID=None
		try:
			self.vCenterID=data['VCenterID']
		except:
			self.vCenterID=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.configStatus=data['ConfigStatus']
		except:
			self.configStatus=None
		try:
			self.overallStatus=data['OverallStatus']
		except:
			self.overallStatus=None
		try:
			self.managedStatus=data['ManagedStatus']
		except:
			self.managedStatus=None

	def getDataCenterID(self):
		return self.dataCenterID
	def getManagedObjectID(self):
		return self.managedObjectID
	def getVCenterID(self):
		return self.vCenterID
	def getName(self):
		return self.name
	def getConfigStatus(self):
		return self.configStatus
	def getOverallStatus(self):
		return self.overallStatus
	def getManagedStatus(self):
		return self.managedStatus

class OrionVIMHostIPAddresses():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.hostID=data['HostID']
		except:
			self.hostID=None
		try:
			self.iPAddress=data['IPAddress']
		except:
			self.iPAddress=None

	def getHostID(self):
		return self.hostID
	def getIPAddress(self):
		return self.iPAddress

class OrionVIMHosts():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.hostID=data['HostID']
		except:
			self.hostID=None
		try:
			self.managedObjectID=data['ManagedObjectID']
		except:
			self.managedObjectID=None
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.hostName=data['HostName']
		except:
			self.hostName=None
		try:
			self.clusterID=data['ClusterID']
		except:
			self.clusterID=None
		try:
			self.dataCenterID=data['DataCenterID']
		except:
			self.dataCenterID=None
		try:
			self.vMwareProductName=data['VMwareProductName']
		except:
			self.vMwareProductName=None
		try:
			self.vMwareProductVersion=data['VMwareProductVersion']
		except:
			self.vMwareProductVersion=None
		try:
			self.pollingJobID=data['PollingJobID']
		except:
			self.pollingJobID=None
		try:
			self.serviceURIID=data['ServiceURIID']
		except:
			self.serviceURIID=None
		try:
			self.credentialID=data['CredentialID']
		except:
			self.credentialID=None
		try:
			self.hostStatus=data['HostStatus']
		except:
			self.hostStatus=None
		try:
			self.pollingMethod=data['PollingMethod']
		except:
			self.pollingMethod=None
		try:
			self.model=data['Model']
		except:
			self.model=None
		try:
			self.vendor=data['Vendor']
		except:
			self.vendor=None
		try:
			self.processorType=data['ProcessorType']
		except:
			self.processorType=None
		try:
			self.cpuCoreCount=data['CpuCoreCount']
		except:
			self.cpuCoreCount=None
		try:
			self.cpuPkgCount=data['CpuPkgCount']
		except:
			self.cpuPkgCount=None
		try:
			self.cpuMhz=data['CpuMhz']
		except:
			self.cpuMhz=None
		try:
			self.nicCount=data['NicCount']
		except:
			self.nicCount=None
		try:
			self.hbaCount=data['HbaCount']
		except:
			self.hbaCount=None
		try:
			self.hbaFcCount=data['HbaFcCount']
		except:
			self.hbaFcCount=None
		try:
			self.hbaScsiCount=data['HbaScsiCount']
		except:
			self.hbaScsiCount=None
		try:
			self.hbaIscsiCount=data['HbaIscsiCount']
		except:
			self.hbaIscsiCount=None
		try:
			self.memorySize=data['MemorySize']
		except:
			self.memorySize=None
		try:
			self.buildNumber=data['BuildNumber']
		except:
			self.buildNumber=None
		try:
			self.biosSerial=data['BiosSerial']
		except:
			self.biosSerial=None
		try:
			self.iPAddress=data['IPAddress']
		except:
			self.iPAddress=None
		try:
			self.connectionState=data['ConnectionState']
		except:
			self.connectionState=None
		try:
			self.configStatus=data['ConfigStatus']
		except:
			self.configStatus=None
		try:
			self.overallStatus=data['OverallStatus']
		except:
			self.overallStatus=None
		try:
			self.nodeStatus=data['NodeStatus']
		except:
			self.nodeStatus=None
		try:
			self.networkUtilization=data['NetworkUtilization']
		except:
			self.networkUtilization=None
		try:
			self.networkUsageRate=data['NetworkUsageRate']
		except:
			self.networkUsageRate=None
		try:
			self.networkTransmitRate=data['NetworkTransmitRate']
		except:
			self.networkTransmitRate=None
		try:
			self.networkReceiveRate=data['NetworkReceiveRate']
		except:
			self.networkReceiveRate=None
		try:
			self.networkCapacityKbps=data['NetworkCapacityKbps']
		except:
			self.networkCapacityKbps=None
		try:
			self.cpuLoad=data['CpuLoad']
		except:
			self.cpuLoad=None
		try:
			self.cpuUsageMHz=data['CpuUsageMHz']
		except:
			self.cpuUsageMHz=None
		try:
			self.memUsage=data['MemUsage']
		except:
			self.memUsage=None
		try:
			self.memUsageMB=data['MemUsageMB']
		except:
			self.memUsageMB=None
		try:
			self.vmCount=data['VmCount']
		except:
			self.vmCount=None
		try:
			self.vmRunningCount=data['VmRunningCount']
		except:
			self.vmRunningCount=None
		try:
			self.statusMessage=data['StatusMessage']
		except:
			self.statusMessage=None
		try:
			self.platformID=data['PlatformID']
		except:
			self.platformID=None

	def getHostID(self):
		return self.hostID
	def getManagedObjectID(self):
		return self.managedObjectID
	def getNodeID(self):
		return self.nodeID
	def getHostName(self):
		return self.hostName
	def getClusterID(self):
		return self.clusterID
	def getDataCenterID(self):
		return self.dataCenterID
	def getVMwareProductName(self):
		return self.vMwareProductName
	def getVMwareProductVersion(self):
		return self.vMwareProductVersion
	def getPollingJobID(self):
		return self.pollingJobID
	def getServiceURIID(self):
		return self.serviceURIID
	def getCredentialID(self):
		return self.credentialID
	def getHostStatus(self):
		return self.hostStatus
	def getPollingMethod(self):
		return self.pollingMethod
	def getModel(self):
		return self.model
	def getVendor(self):
		return self.vendor
	def getProcessorType(self):
		return self.processorType
	def getCpuCoreCount(self):
		return self.cpuCoreCount
	def getCpuPkgCount(self):
		return self.cpuPkgCount
	def getCpuMhz(self):
		return self.cpuMhz
	def getNicCount(self):
		return self.nicCount
	def getHbaCount(self):
		return self.hbaCount
	def getHbaFcCount(self):
		return self.hbaFcCount
	def getHbaScsiCount(self):
		return self.hbaScsiCount
	def getHbaIscsiCount(self):
		return self.hbaIscsiCount
	def getMemorySize(self):
		return self.memorySize
	def getBuildNumber(self):
		return self.buildNumber
	def getBiosSerial(self):
		return self.biosSerial
	def getIPAddress(self):
		return self.iPAddress
	def getConnectionState(self):
		return self.connectionState
	def getConfigStatus(self):
		return self.configStatus
	def getOverallStatus(self):
		return self.overallStatus
	def getNodeStatus(self):
		return self.nodeStatus
	def getNetworkUtilization(self):
		return self.networkUtilization
	def getNetworkUsageRate(self):
		return self.networkUsageRate
	def getNetworkTransmitRate(self):
		return self.networkTransmitRate
	def getNetworkReceiveRate(self):
		return self.networkReceiveRate
	def getNetworkCapacityKbps(self):
		return self.networkCapacityKbps
	def getCpuLoad(self):
		return self.cpuLoad
	def getCpuUsageMHz(self):
		return self.cpuUsageMHz
	def getMemUsage(self):
		return self.memUsage
	def getMemUsageMB(self):
		return self.memUsageMB
	def getVmCount(self):
		return self.vmCount
	def getVmRunningCount(self):
		return self.vmRunningCount
	def getStatusMessage(self):
		return self.statusMessage
	def getPlatformID(self):
		return self.platformID

class OrionVIMHostStatistics():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.hostID=data['HostID']
		except:
			self.hostID=None
		try:
			self.dateTime=data['DateTime']
		except:
			self.dateTime=None
		try:
			self.vmCount=data['VmCount']
		except:
			self.vmCount=None
		try:
			self.vmRunningCount=data['VmRunningCount']
		except:
			self.vmRunningCount=None
		try:
			self.minNetworkUtilization=data['MinNetworkUtilization']
		except:
			self.minNetworkUtilization=None
		try:
			self.maxNetworkUtilization=data['MaxNetworkUtilization']
		except:
			self.maxNetworkUtilization=None
		try:
			self.avgNetworkUtilization=data['AvgNetworkUtilization']
		except:
			self.avgNetworkUtilization=None
		try:
			self.minNetworkUsageRate=data['MinNetworkUsageRate']
		except:
			self.minNetworkUsageRate=None
		try:
			self.maxNetworkUsageRate=data['MaxNetworkUsageRate']
		except:
			self.maxNetworkUsageRate=None
		try:
			self.avgNetworkUsageRate=data['AvgNetworkUsageRate']
		except:
			self.avgNetworkUsageRate=None
		try:
			self.minNetworkTransmitRate=data['MinNetworkTransmitRate']
		except:
			self.minNetworkTransmitRate=None
		try:
			self.maxNetworkTransmitRate=data['MaxNetworkTransmitRate']
		except:
			self.maxNetworkTransmitRate=None
		try:
			self.avgNetworkTransmitRate=data['AvgNetworkTransmitRate']
		except:
			self.avgNetworkTransmitRate=None
		try:
			self.minNetworkReceiveRate=data['MinNetworkReceiveRate']
		except:
			self.minNetworkReceiveRate=None
		try:
			self.maxNetworkReceiveRate=data['MaxNetworkReceiveRate']
		except:
			self.maxNetworkReceiveRate=None
		try:
			self.avgNetworkReceiveRate=data['AvgNetworkReceiveRate']
		except:
			self.avgNetworkReceiveRate=None

	def getHostID(self):
		return self.hostID
	def getDateTime(self):
		return self.dateTime
	def getVmCount(self):
		return self.vmCount
	def getVmRunningCount(self):
		return self.vmRunningCount
	def getMinNetworkUtilization(self):
		return self.minNetworkUtilization
	def getMaxNetworkUtilization(self):
		return self.maxNetworkUtilization
	def getAvgNetworkUtilization(self):
		return self.avgNetworkUtilization
	def getMinNetworkUsageRate(self):
		return self.minNetworkUsageRate
	def getMaxNetworkUsageRate(self):
		return self.maxNetworkUsageRate
	def getAvgNetworkUsageRate(self):
		return self.avgNetworkUsageRate
	def getMinNetworkTransmitRate(self):
		return self.minNetworkTransmitRate
	def getMaxNetworkTransmitRate(self):
		return self.maxNetworkTransmitRate
	def getAvgNetworkTransmitRate(self):
		return self.avgNetworkTransmitRate
	def getMinNetworkReceiveRate(self):
		return self.minNetworkReceiveRate
	def getMaxNetworkReceiveRate(self):
		return self.maxNetworkReceiveRate
	def getAvgNetworkReceiveRate(self):
		return self.avgNetworkReceiveRate

class OrionVIMManagedEntity():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.status=data['Status']
		except:
			self.status=None
		try:
			self.statusDescription=data['StatusDescription']
		except:
			self.statusDescription=None
		try:
			self.statusLED=data['StatusLED']
		except:
			self.statusLED=None
		try:
			self.unManaged=data['UnManaged']
		except:
			self.unManaged=None
		try:
			self.unManageFrom=data['UnManageFrom']
		except:
			self.unManageFrom=None
		try:
			self.unManageUntil=data['UnManageUntil']
		except:
			self.unManageUntil=None
		try:
			self.triggeredAlarmDescription=data['TriggeredAlarmDescription']
		except:
			self.triggeredAlarmDescription=None
		try:
			self.detailsUrl=data['DetailsUrl']
		except:
			self.detailsUrl=None
		try:
			self.image=data['Image']
		except:
			self.image=None

	def getStatus(self):
		return self.status
	def getStatusDescription(self):
		return self.statusDescription
	def getStatusLED(self):
		return self.statusLED
	def getUnManaged(self):
		return self.unManaged
	def getUnManageFrom(self):
		return self.unManageFrom
	def getUnManageUntil(self):
		return self.unManageUntil
	def getTriggeredAlarmDescription(self):
		return self.triggeredAlarmDescription
	def getDetailsUrl(self):
		return self.detailsUrl
	def getImage(self):
		return self.image

class OrionVIMResourcePools():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.resourcePoolID=data['ResourcePoolID']
		except:
			self.resourcePoolID=None
		try:
			self.managedObjectID=data['ManagedObjectID']
		except:
			self.managedObjectID=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.cpuMaxUsage=data['CpuMaxUsage']
		except:
			self.cpuMaxUsage=None
		try:
			self.cpuOverallUsage=data['CpuOverallUsage']
		except:
			self.cpuOverallUsage=None
		try:
			self.cpuReservationUsedForVM=data['CpuReservationUsedForVM']
		except:
			self.cpuReservationUsedForVM=None
		try:
			self.cpuReservationUsed=data['CpuReservationUsed']
		except:
			self.cpuReservationUsed=None
		try:
			self.memMaxUsage=data['MemMaxUsage']
		except:
			self.memMaxUsage=None
		try:
			self.memOverallUsage=data['MemOverallUsage']
		except:
			self.memOverallUsage=None
		try:
			self.memReservationUsedForVM=data['MemReservationUsedForVM']
		except:
			self.memReservationUsedForVM=None
		try:
			self.memReservationUsed=data['MemReservationUsed']
		except:
			self.memReservationUsed=None
		try:
			self.lastModifiedTime=data['LastModifiedTime']
		except:
			self.lastModifiedTime=None
		try:
			self.cpuExpandable=data['CpuExpandable']
		except:
			self.cpuExpandable=None
		try:
			self.cpuLimit=data['CpuLimit']
		except:
			self.cpuLimit=None
		try:
			self.cpuReservation=data['CpuReservation']
		except:
			self.cpuReservation=None
		try:
			self.cpuShareLevel=data['CpuShareLevel']
		except:
			self.cpuShareLevel=None
		try:
			self.cpuShareCount=data['CpuShareCount']
		except:
			self.cpuShareCount=None
		try:
			self.memExpandable=data['MemExpandable']
		except:
			self.memExpandable=None
		try:
			self.memLimit=data['MemLimit']
		except:
			self.memLimit=None
		try:
			self.memReservation=data['MemReservation']
		except:
			self.memReservation=None
		try:
			self.memShareLevel=data['MemShareLevel']
		except:
			self.memShareLevel=None
		try:
			self.memShareCount=data['MemShareCount']
		except:
			self.memShareCount=None
		try:
			self.configStatus=data['ConfigStatus']
		except:
			self.configStatus=None
		try:
			self.overallStatus=data['OverallStatus']
		except:
			self.overallStatus=None
		try:
			self.managedStatus=data['ManagedStatus']
		except:
			self.managedStatus=None
		try:
			self.clusterID=data['ClusterID']
		except:
			self.clusterID=None
		try:
			self.vCenterID=data['VCenterID']
		except:
			self.vCenterID=None
		try:
			self.parentResourcePoolID=data['ParentResourcePoolID']
		except:
			self.parentResourcePoolID=None

	def getResourcePoolID(self):
		return self.resourcePoolID
	def getManagedObjectID(self):
		return self.managedObjectID
	def getName(self):
		return self.name
	def getCpuMaxUsage(self):
		return self.cpuMaxUsage
	def getCpuOverallUsage(self):
		return self.cpuOverallUsage
	def getCpuReservationUsedForVM(self):
		return self.cpuReservationUsedForVM
	def getCpuReservationUsed(self):
		return self.cpuReservationUsed
	def getMemMaxUsage(self):
		return self.memMaxUsage
	def getMemOverallUsage(self):
		return self.memOverallUsage
	def getMemReservationUsedForVM(self):
		return self.memReservationUsedForVM
	def getMemReservationUsed(self):
		return self.memReservationUsed
	def getLastModifiedTime(self):
		return self.lastModifiedTime
	def getCpuExpandable(self):
		return self.cpuExpandable
	def getCpuLimit(self):
		return self.cpuLimit
	def getCpuReservation(self):
		return self.cpuReservation
	def getCpuShareLevel(self):
		return self.cpuShareLevel
	def getCpuShareCount(self):
		return self.cpuShareCount
	def getMemExpandable(self):
		return self.memExpandable
	def getMemLimit(self):
		return self.memLimit
	def getMemReservation(self):
		return self.memReservation
	def getMemShareLevel(self):
		return self.memShareLevel
	def getMemShareCount(self):
		return self.memShareCount
	def getConfigStatus(self):
		return self.configStatus
	def getOverallStatus(self):
		return self.overallStatus
	def getManagedStatus(self):
		return self.managedStatus
	def getClusterID(self):
		return self.clusterID
	def getVCenterID(self):
		return self.vCenterID
	def getParentResourcePoolID(self):
		return self.parentResourcePoolID

class OrionVIMThresholds():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.thresholdID=data['ThresholdID']
		except:
			self.thresholdID=None
		try:
			self.typeID=data['TypeID']
		except:
			self.typeID=None
		try:
			self.warning=data['Warning']
		except:
			self.warning=None
		try:
			self.high=data['High']
		except:
			self.high=None
		try:
			self.maximum=data['Maximum']
		except:
			self.maximum=None

	def getThresholdID(self):
		return self.thresholdID
	def getTypeID(self):
		return self.typeID
	def getWarning(self):
		return self.warning
	def getHigh(self):
		return self.high
	def getMaximum(self):
		return self.maximum

class OrionVIMThresholdTypes():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.typeID=data['TypeID']
		except:
			self.typeID=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.information=data['Information']
		except:
			self.information=None
		try:
			self.warning=data['Warning']
		except:
			self.warning=None
		try:
			self.high=data['High']
		except:
			self.high=None
		try:
			self.maximum=data['Maximum']
		except:
			self.maximum=None

	def getTypeID(self):
		return self.typeID
	def getName(self):
		return self.name
	def getInformation(self):
		return self.information
	def getWarning(self):
		return self.warning
	def getHigh(self):
		return self.high
	def getMaximum(self):
		return self.maximum

class OrionVIMVCenters():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.vCenterID=data['VCenterID']
		except:
			self.vCenterID=None
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.vMwareProductName=data['VMwareProductName']
		except:
			self.vMwareProductName=None
		try:
			self.vMwareProductVersion=data['VMwareProductVersion']
		except:
			self.vMwareProductVersion=None
		try:
			self.pollingJobID=data['PollingJobID']
		except:
			self.pollingJobID=None
		try:
			self.serviceURIID=data['ServiceURIID']
		except:
			self.serviceURIID=None
		try:
			self.credentialID=data['CredentialID']
		except:
			self.credentialID=None
		try:
			self.hostStatus=data['HostStatus']
		except:
			self.hostStatus=None
		try:
			self.model=data['Model']
		except:
			self.model=None
		try:
			self.vendor=data['Vendor']
		except:
			self.vendor=None
		try:
			self.buildNumber=data['BuildNumber']
		except:
			self.buildNumber=None
		try:
			self.biosSerial=data['BiosSerial']
		except:
			self.biosSerial=None
		try:
			self.iPAddress=data['IPAddress']
		except:
			self.iPAddress=None
		try:
			self.connectionState=data['ConnectionState']
		except:
			self.connectionState=None
		try:
			self.statusMessage=data['StatusMessage']
		except:
			self.statusMessage=None

	def getVCenterID(self):
		return self.vCenterID
	def getNodeID(self):
		return self.nodeID
	def getName(self):
		return self.name
	def getVMwareProductName(self):
		return self.vMwareProductName
	def getVMwareProductVersion(self):
		return self.vMwareProductVersion
	def getPollingJobID(self):
		return self.pollingJobID
	def getServiceURIID(self):
		return self.serviceURIID
	def getCredentialID(self):
		return self.credentialID
	def getHostStatus(self):
		return self.hostStatus
	def getModel(self):
		return self.model
	def getVendor(self):
		return self.vendor
	def getBuildNumber(self):
		return self.buildNumber
	def getBiosSerial(self):
		return self.biosSerial
	def getIPAddress(self):
		return self.iPAddress
	def getConnectionState(self):
		return self.connectionState
	def getStatusMessage(self):
		return self.statusMessage

class OrionVIMVirtualMachines():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.virtualMachineID=data['VirtualMachineID']
		except:
			self.virtualMachineID=None
		try:
			self.managedObjectID=data['ManagedObjectID']
		except:
			self.managedObjectID=None
		try:
			self.uUID=data['UUID']
		except:
			self.uUID=None
		try:
			self.hostID=data['HostID']
		except:
			self.hostID=None
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.resourcePoolID=data['ResourcePoolID']
		except:
			self.resourcePoolID=None
		try:
			self.vMConfigFile=data['VMConfigFile']
		except:
			self.vMConfigFile=None
		try:
			self.memoryConfigured=data['MemoryConfigured']
		except:
			self.memoryConfigured=None
		try:
			self.memoryShares=data['MemoryShares']
		except:
			self.memoryShares=None
		try:
			self.cPUShares=data['CPUShares']
		except:
			self.cPUShares=None
		try:
			self.guestState=data['GuestState']
		except:
			self.guestState=None
		try:
			self.iPAddress=data['IPAddress']
		except:
			self.iPAddress=None
		try:
			self.logDirectory=data['LogDirectory']
		except:
			self.logDirectory=None
		try:
			self.guestVmWareToolsVersion=data['GuestVmWareToolsVersion']
		except:
			self.guestVmWareToolsVersion=None
		try:
			self.guestVmWareToolsStatus=data['GuestVmWareToolsStatus']
		except:
			self.guestVmWareToolsStatus=None
		try:
			self.name=data['Name']
		except:
			self.name=None
		try:
			self.guestName=data['GuestName']
		except:
			self.guestName=None
		try:
			self.guestFamily=data['GuestFamily']
		except:
			self.guestFamily=None
		try:
			self.guestDnsName=data['GuestDnsName']
		except:
			self.guestDnsName=None
		try:
			self.nicCount=data['NicCount']
		except:
			self.nicCount=None
		try:
			self.vDisksCount=data['VDisksCount']
		except:
			self.vDisksCount=None
		try:
			self.processorCount=data['ProcessorCount']
		except:
			self.processorCount=None
		try:
			self.powerState=data['PowerState']
		except:
			self.powerState=None
		try:
			self.bootTime=data['BootTime']
		except:
			self.bootTime=None
		try:
			self.configStatus=data['ConfigStatus']
		except:
			self.configStatus=None
		try:
			self.overallStatus=data['OverallStatus']
		except:
			self.overallStatus=None
		try:
			self.nodeStatus=data['NodeStatus']
		except:
			self.nodeStatus=None
		try:
			self.networkUsageRate=data['NetworkUsageRate']
		except:
			self.networkUsageRate=None
		try:
			self.networkTransmitRate=data['NetworkTransmitRate']
		except:
			self.networkTransmitRate=None
		try:
			self.networkReceiveRate=data['NetworkReceiveRate']
		except:
			self.networkReceiveRate=None
		try:
			self.cpuLoad=data['CpuLoad']
		except:
			self.cpuLoad=None
		try:
			self.cpuUsageMHz=data['CpuUsageMHz']
		except:
			self.cpuUsageMHz=None
		try:
			self.memUsage=data['MemUsage']
		except:
			self.memUsage=None
		try:
			self.memUsageMB=data['MemUsageMB']
		except:
			self.memUsageMB=None
		try:
			self.isLicensed=data['IsLicensed']
		except:
			self.isLicensed=None

	def getVirtualMachineID(self):
		return self.virtualMachineID
	def getManagedObjectID(self):
		return self.managedObjectID
	def getUUID(self):
		return self.uUID
	def getHostID(self):
		return self.hostID
	def getNodeID(self):
		return self.nodeID
	def getResourcePoolID(self):
		return self.resourcePoolID
	def getVMConfigFile(self):
		return self.vMConfigFile
	def getMemoryConfigured(self):
		return self.memoryConfigured
	def getMemoryShares(self):
		return self.memoryShares
	def getCPUShares(self):
		return self.cPUShares
	def getGuestState(self):
		return self.guestState
	def getIPAddress(self):
		return self.iPAddress
	def getLogDirectory(self):
		return self.logDirectory
	def getGuestVmWareToolsVersion(self):
		return self.guestVmWareToolsVersion
	def getGuestVmWareToolsStatus(self):
		return self.guestVmWareToolsStatus
	def getName(self):
		return self.name
	def getGuestName(self):
		return self.guestName
	def getGuestFamily(self):
		return self.guestFamily
	def getGuestDnsName(self):
		return self.guestDnsName
	def getNicCount(self):
		return self.nicCount
	def getVDisksCount(self):
		return self.vDisksCount
	def getProcessorCount(self):
		return self.processorCount
	def getPowerState(self):
		return self.powerState
	def getBootTime(self):
		return self.bootTime
	def getConfigStatus(self):
		return self.configStatus
	def getOverallStatus(self):
		return self.overallStatus
	def getNodeStatus(self):
		return self.nodeStatus
	def getNetworkUsageRate(self):
		return self.networkUsageRate
	def getNetworkTransmitRate(self):
		return self.networkTransmitRate
	def getNetworkReceiveRate(self):
		return self.networkReceiveRate
	def getCpuLoad(self):
		return self.cpuLoad
	def getCpuUsageMHz(self):
		return self.cpuUsageMHz
	def getMemUsage(self):
		return self.memUsage
	def getMemUsageMB(self):
		return self.memUsageMB
	def getIsLicensed(self):
		return self.isLicensed

class OrionVIMVMStatistics():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.virtualMachineID=data['VirtualMachineID']
		except:
			self.virtualMachineID=None
		try:
			self.dateTime=data['DateTime']
		except:
			self.dateTime=None
		try:
			self.minCPULoad=data['MinCPULoad']
		except:
			self.minCPULoad=None
		try:
			self.maxCPULoad=data['MaxCPULoad']
		except:
			self.maxCPULoad=None
		try:
			self.avgCPULoad=data['AvgCPULoad']
		except:
			self.avgCPULoad=None
		try:
			self.minMemoryUsage=data['MinMemoryUsage']
		except:
			self.minMemoryUsage=None
		try:
			self.maxMemoryUsage=data['MaxMemoryUsage']
		except:
			self.maxMemoryUsage=None
		try:
			self.avgMemoryUsage=data['AvgMemoryUsage']
		except:
			self.avgMemoryUsage=None
		try:
			self.minNetworkUsageRate=data['MinNetworkUsageRate']
		except:
			self.minNetworkUsageRate=None
		try:
			self.maxNetworkUsageRate=data['MaxNetworkUsageRate']
		except:
			self.maxNetworkUsageRate=None
		try:
			self.avgNetworkUsageRate=data['AvgNetworkUsageRate']
		except:
			self.avgNetworkUsageRate=None
		try:
			self.minNetworkTransmitRate=data['MinNetworkTransmitRate']
		except:
			self.minNetworkTransmitRate=None
		try:
			self.maxNetworkTransmitRate=data['MaxNetworkTransmitRate']
		except:
			self.maxNetworkTransmitRate=None
		try:
			self.avgNetworkTransmitRate=data['AvgNetworkTransmitRate']
		except:
			self.avgNetworkTransmitRate=None
		try:
			self.minNetworkReceiveRate=data['MinNetworkReceiveRate']
		except:
			self.minNetworkReceiveRate=None
		try:
			self.maxNetworkReceiveRate=data['MaxNetworkReceiveRate']
		except:
			self.maxNetworkReceiveRate=None
		try:
			self.avgNetworkReceiveRate=data['AvgNetworkReceiveRate']
		except:
			self.avgNetworkReceiveRate=None
		try:
			self.availability=data['Availability']
		except:
			self.availability=None

	def getVirtualMachineID(self):
		return self.virtualMachineID
	def getDateTime(self):
		return self.dateTime
	def getMinCPULoad(self):
		return self.minCPULoad
	def getMaxCPULoad(self):
		return self.maxCPULoad
	def getAvgCPULoad(self):
		return self.avgCPULoad
	def getMinMemoryUsage(self):
		return self.minMemoryUsage
	def getMaxMemoryUsage(self):
		return self.maxMemoryUsage
	def getAvgMemoryUsage(self):
		return self.avgMemoryUsage
	def getMinNetworkUsageRate(self):
		return self.minNetworkUsageRate
	def getMaxNetworkUsageRate(self):
		return self.maxNetworkUsageRate
	def getAvgNetworkUsageRate(self):
		return self.avgNetworkUsageRate
	def getMinNetworkTransmitRate(self):
		return self.minNetworkTransmitRate
	def getMaxNetworkTransmitRate(self):
		return self.maxNetworkTransmitRate
	def getAvgNetworkTransmitRate(self):
		return self.avgNetworkTransmitRate
	def getMinNetworkReceiveRate(self):
		return self.minNetworkReceiveRate
	def getMaxNetworkReceiveRate(self):
		return self.maxNetworkReceiveRate
	def getAvgNetworkReceiveRate(self):
		return self.avgNetworkReceiveRate
	def getAvailability(self):
		return self.availability

class OrionVolumePerformanceHistory():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.volumeID=data['VolumeID']
		except:
			self.volumeID=None
		try:
			self.dateTime=data['DateTime']
		except:
			self.dateTime=None
		try:
			self.avgDiskQueueLength=data['AvgDiskQueueLength']
		except:
			self.avgDiskQueueLength=None
		try:
			self.minDiskQueueLength=data['MinDiskQueueLength']
		except:
			self.minDiskQueueLength=None
		try:
			self.maxDiskQueueLength=data['MaxDiskQueueLength']
		except:
			self.maxDiskQueueLength=None
		try:
			self.avgDiskTransfer=data['AvgDiskTransfer']
		except:
			self.avgDiskTransfer=None
		try:
			self.minDiskTransfer=data['MinDiskTransfer']
		except:
			self.minDiskTransfer=None
		try:
			self.maxDiskTransfer=data['MaxDiskTransfer']
		except:
			self.maxDiskTransfer=None
		try:
			self.avgDiskReads=data['AvgDiskReads']
		except:
			self.avgDiskReads=None
		try:
			self.minDiskReads=data['MinDiskReads']
		except:
			self.minDiskReads=None
		try:
			self.maxDiskReads=data['MaxDiskReads']
		except:
			self.maxDiskReads=None
		try:
			self.avgDiskWrites=data['AvgDiskWrites']
		except:
			self.avgDiskWrites=None
		try:
			self.minDiskWrites=data['MinDiskWrites']
		except:
			self.minDiskWrites=None
		try:
			self.maxDiskWrites=data['MaxDiskWrites']
		except:
			self.maxDiskWrites=None

	def getNodeID(self):
		return self.nodeID
	def getVolumeID(self):
		return self.volumeID
	def getDateTime(self):
		return self.dateTime
	def getAvgDiskQueueLength(self):
		return self.avgDiskQueueLength
	def getMinDiskQueueLength(self):
		return self.minDiskQueueLength
	def getMaxDiskQueueLength(self):
		return self.maxDiskQueueLength
	def getAvgDiskTransfer(self):
		return self.avgDiskTransfer
	def getMinDiskTransfer(self):
		return self.minDiskTransfer
	def getMaxDiskTransfer(self):
		return self.maxDiskTransfer
	def getAvgDiskReads(self):
		return self.avgDiskReads
	def getMinDiskReads(self):
		return self.minDiskReads
	def getMaxDiskReads(self):
		return self.maxDiskReads
	def getAvgDiskWrites(self):
		return self.avgDiskWrites
	def getMinDiskWrites(self):
		return self.minDiskWrites
	def getMaxDiskWrites(self):
		return self.maxDiskWrites

class OrionVolumes():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.volumeID=data['VolumeID']
		except:
			self.volumeID=None
		try:
			self.icon=data['Icon']
		except:
			self.icon=None
		try:
			self.index=data['Index']
		except:
			self.index=None
		try:
			self.caption=data['Caption']
		except:
			self.caption=None
		try:
			self.pollInterval=data['PollInterval']
		except:
			self.pollInterval=None
		try:
			self.statCollection=data['StatCollection']
		except:
			self.statCollection=None
		try:
			self.rediscoveryInterval=data['RediscoveryInterval']
		except:
			self.rediscoveryInterval=None
		try:
			self.statusIcon=data['StatusIcon']
		except:
			self.statusIcon=None
		try:
			self.type=data['Type']
		except:
			self.type=None
		try:
			self.size=data['Size']
		except:
			self.size=None
		try:
			self.responding=data['Responding']
		except:
			self.responding=None
		try:
			self.fullName=data['FullName']
		except:
			self.fullName=None
		try:
			self.lastSync=data['LastSync']
		except:
			self.lastSync=None
		try:
			self.volumePercentUsed=data['VolumePercentUsed']
		except:
			self.volumePercentUsed=None
		try:
			self.volumeAllocationFailuresThisHour=data['VolumeAllocationFailuresThisHour']
		except:
			self.volumeAllocationFailuresThisHour=None
		try:
			self.volumeIndex=data['VolumeIndex']
		except:
			self.volumeIndex=None
		try:
			self.volumeType=data['VolumeType']
		except:
			self.volumeType=None
		try:
			self.volumeDescription=data['VolumeDescription']
		except:
			self.volumeDescription=None
		try:
			self.volumeSize=data['VolumeSize']
		except:
			self.volumeSize=None
		try:
			self.volumeSpaceUsed=data['VolumeSpaceUsed']
		except:
			self.volumeSpaceUsed=None
		try:
			self.volumeAllocationFailuresToday=data['VolumeAllocationFailuresToday']
		except:
			self.volumeAllocationFailuresToday=None
		try:
			self.volumeResponding=data['VolumeResponding']
		except:
			self.volumeResponding=None
		try:
			self.volumeSpaceAvailable=data['VolumeSpaceAvailable']
		except:
			self.volumeSpaceAvailable=None
		try:
			self.volumeTypeIcon=data['VolumeTypeIcon']
		except:
			self.volumeTypeIcon=None
		try:
			self.orionIdPrefix=data['OrionIdPrefix']
		except:
			self.orionIdPrefix=None
		try:
			self.orionIdColumn=data['OrionIdColumn']
		except:
			self.orionIdColumn=None
		try:
			self.diskQueueLength=data['DiskQueueLength']
		except:
			self.diskQueueLength=None
		try:
			self.diskTransfer=data['DiskTransfer']
		except:
			self.diskTransfer=None
		try:
			self.diskReads=data['DiskReads']
		except:
			self.diskReads=None
		try:
			self.diskWrites=data['DiskWrites']
		except:
			self.diskWrites=None
		try:
			self.totalDiskIOPS=data['TotalDiskIOPS']
		except:
			self.totalDiskIOPS=None

	def getNodeID(self):
		return self.nodeID
	def getVolumeID(self):
		return self.volumeID
	def getIcon(self):
		return self.icon
	def getIndex(self):
		return self.index
	def getCaption(self):
		return self.caption
	def getPollInterval(self):
		return self.pollInterval
	def getStatCollection(self):
		return self.statCollection
	def getRediscoveryInterval(self):
		return self.rediscoveryInterval
	def getStatusIcon(self):
		return self.statusIcon
	def getType(self):
		return self.type
	def getSize(self):
		return self.size
	def getResponding(self):
		return self.responding
	def getFullName(self):
		return self.fullName
	def getLastSync(self):
		return self.lastSync
	def getVolumePercentUsed(self):
		return self.volumePercentUsed
	def getVolumeAllocationFailuresThisHour(self):
		return self.volumeAllocationFailuresThisHour
	def getVolumeIndex(self):
		return self.volumeIndex
	def getVolumeType(self):
		return self.volumeType
	def getVolumeDescription(self):
		return self.volumeDescription
	def getVolumeSize(self):
		return self.volumeSize
	def getVolumeSpaceUsed(self):
		return self.volumeSpaceUsed
	def getVolumeAllocationFailuresToday(self):
		return self.volumeAllocationFailuresToday
	def getVolumeResponding(self):
		return self.volumeResponding
	def getVolumeSpaceAvailable(self):
		return self.volumeSpaceAvailable
	def getVolumeTypeIcon(self):
		return self.volumeTypeIcon
	def getOrionIdPrefix(self):
		return self.orionIdPrefix
	def getOrionIdColumn(self):
		return self.orionIdColumn
	def getDiskQueueLength(self):
		return self.diskQueueLength
	def getDiskTransfer(self):
		return self.diskTransfer
	def getDiskReads(self):
		return self.diskReads
	def getDiskWrites(self):
		return self.diskWrites
	def getTotalDiskIOPS(self):
		return self.totalDiskIOPS

class OrionVolumesStats():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.percentUsed=data['PercentUsed']
		except:
			self.percentUsed=None
		try:
			self.spaceUsed=data['SpaceUsed']
		except:
			self.spaceUsed=None
		try:
			self.spaceAvailable=data['SpaceAvailable']
		except:
			self.spaceAvailable=None
		try:
			self.allocationFailuresThisHour=data['AllocationFailuresThisHour']
		except:
			self.allocationFailuresThisHour=None
		try:
			self.allocationFailuresToday=data['AllocationFailuresToday']
		except:
			self.allocationFailuresToday=None
		try:
			self.diskQueueLength=data['DiskQueueLength']
		except:
			self.diskQueueLength=None
		try:
			self.diskTransfer=data['DiskTransfer']
		except:
			self.diskTransfer=None
		try:
			self.diskReads=data['DiskReads']
		except:
			self.diskReads=None
		try:
			self.diskWrites=data['DiskWrites']
		except:
			self.diskWrites=None
		try:
			self.totalDiskIOPS=data['TotalDiskIOPS']
		except:
			self.totalDiskIOPS=None
		try:
			self.volumeID=data['VolumeID']
		except:
			self.volumeID=None

	def getPercentUsed(self):
		return self.percentUsed
	def getSpaceUsed(self):
		return self.spaceUsed
	def getSpaceAvailable(self):
		return self.spaceAvailable
	def getAllocationFailuresThisHour(self):
		return self.allocationFailuresThisHour
	def getAllocationFailuresToday(self):
		return self.allocationFailuresToday
	def getDiskQueueLength(self):
		return self.diskQueueLength
	def getDiskTransfer(self):
		return self.diskTransfer
	def getDiskReads(self):
		return self.diskReads
	def getDiskWrites(self):
		return self.diskWrites
	def getTotalDiskIOPS(self):
		return self.totalDiskIOPS
	def getVolumeID(self):
		return self.volumeID

class OrionVolumeUsageHistory():

	def __init__(self,**kwargs):
		requiredArgs=[]
		optionalArgs=['data', 'connection']
		ar=argChecker(requiredArgs,optionalArgs,kwargs.iteritems())
		data=ar['data']
		self.data=ar['data']
		self.connection=ar['connection']
		try:
			self.nodeID=data['NodeID']
		except:
			self.nodeID=None
		try:
			self.volumeID=data['VolumeID']
		except:
			self.volumeID=None
		try:
			self.dateTime=data['DateTime']
		except:
			self.dateTime=None
		try:
			self.diskSize=data['DiskSize']
		except:
			self.diskSize=None
		try:
			self.avgDiskUsed=data['AvgDiskUsed']
		except:
			self.avgDiskUsed=None
		try:
			self.minDiskUsed=data['MinDiskUsed']
		except:
			self.minDiskUsed=None
		try:
			self.maxDiskUsed=data['MaxDiskUsed']
		except:
			self.maxDiskUsed=None
		try:
			self.percentDiskUsed=data['PercentDiskUsed']
		except:
			self.percentDiskUsed=None
		try:
			self.allocationFailures=data['AllocationFailures']
		except:
			self.allocationFailures=None

	def getNodeID(self):
		return self.nodeID
	def getVolumeID(self):
		return self.volumeID
	def getDateTime(self):
		return self.dateTime
	def getDiskSize(self):
		return self.diskSize
	def getAvgDiskUsed(self):
		return self.avgDiskUsed
	def getMinDiskUsed(self):
		return self.minDiskUsed
	def getMaxDiskUsed(self):
		return self.maxDiskUsed
	def getPercentDiskUsed(self):
		return self.percentDiskUsed
	def getAllocationFailures(self):
		return self.allocationFailures
