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
import base64
import httplib
import json
import inspect

from swCommonLib import (
    argChecker,
    debugPrint,
    convertFieldListToSelect,
    convertSelectListToSelect,
    convertWhereListToWhere,
    convertSelectWhereListToSelectWhere,
)

#
# Main SolarWinds class.
# Instantiate an object of this class, with valid credentials as arguments
# and call appropriate 'get' method to retrieve data from SolarWinds db
#


class SolarWinds():

    def __init__(self, **kwargs):
        requiredArgs = ["ip"]
        optionalArgs = ["username", "password", "auth_key", "port"]
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        if not ar:
            print '####### Bad args, no IP set'
        self.ip = ar['ip']
        self.username = ar['username']
        self.password = ar['password']
        self.auth_key = ar['auth_key']
        if ar['port']:
            self.port = ar['port']
        else:
            self.port = 17778

        # special checking need to see either username or auth_key, blank
        # password is valid
        if not ar['username'] and not ar['auth_key']:
            print '####### Bad args, no username/password or auth_key'

        self.connection = None
        self.header = self.createHeader()

    def connect(self):
        # Create connection
        return self.https()

    def https(self):
        httplib.HTTPSConnection.debuglevel = 1
        return httplib.HTTPSConnection(self.ip, self.port)

    def createHeader(self):
        # Set the correct html header which could be device specific
        header = {
            'Accept': 'application/json',
            "Content-Type": "application/json"}
        # Use the auth_key if its there, else encode the username/password
        if not self.auth_key:
            self.auth_key = base64.encodestring(
                '%s:%s' %
                (self.username, self.password))
        # Create the final header
        header['authorization'] = 'Basic %s' % self.auth_key
        return header

    def sendRequest(self, **kwargs):
        requiredArgs = ["Type", "URL", "status"]
        optionalArgs = ["payload"]
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        payload = ar['payload']
        Type = ar['Type']
        URL = ar['URL']
        status = ar['status']

        conn = self.connect()
        caller = inspect.stack()

    # This allows us to dump the calling function in case of errors

        if payload:
            payload = json.dumps(payload, ensure_ascii=False)
            payload.encode('utf-8')

        # Attempt to connect using the given details.
        # If the connection fails, return False and dump the calling function

        debugPrint("In sendRequest")
        debugPrint("Type = %s" % (Type))
        debugPrint("URL = %s" % (URL))
        debugPrint("payload = %s" % (payload))
        debugPrint("header = %s" % (self.header))
        try:
            conn.request(Type, URL, payload, self.header)
        except:
            print "Could not connect in call from %s. Unable to continue" % (caller)
            return None
        # If we are here, the connection was successful, now we need to ensure
        # that we got a response that we were expecting.
        response = conn.getresponse()
        debugPrint(
            "Response header = %s" %
            (response.getheaders()))
        # status is passed into the call and is the http response status expeted from the call.
        # If the passed in status is 0, ifgnore this check
        if status:
                        # if we dont get the response we expected, we must stop
            if response.status != status:
                print "Received HTTP response %s from %s. Caller is %s. Unable to continue" % (response.status, self.ip, caller)
                return None
        # Not all data can be passed back as a json.loads format. Try to pass it back in this format
        # but if it fails, just pass it back unformatted.
        try:
            data = json.loads(response.read())
        except:
            data = response.read()
        # return the data
        return data

    def getOrionAccounts(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionAccountsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'AccountID',
            'Enabled',
            'AllowNodeManagement',
            'AllowAdmin',
            'CanClearEvents',
            'AllowReportManagement',
            'Expires',
            'LastLogin',
            'LimitationID1',
            'LimitationID2',
            'LimitationID3',
            'AccountSID',
            'AccountType']
        tableName = 'Orion.Accounts'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionAccounts = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionAccounts is None:
                return []
        for obj in currOrionAccounts['results']:
            thisObj = OrionAccounts(connection=self, data=obj)
            self.orionAccountsObjs.append(thisObj)
        return self.orionAccountsObjs

    def getOrionActiveAlerts(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionActiveAlertsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'AlertID',
            'AlertTime',
            'ObjectType',
            'ObjectID',
            'ObjectName',
            'NodeID',
            'NodeName',
            'EventMessage',
            'propertyID',
            'Monitoredproperty',
            'CurrentValue',
            'TriggerValue',
            'ResetValue',
            'EngineID',
            'AlertNotes',
            'ExpireTime']
        tableName = 'Orion.ActiveAlerts'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionActiveAlerts = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionActiveAlerts is None:
                return []
        for obj in currOrionActiveAlerts['results']:
            thisObj = OrionActiveAlerts(connection=self, data=obj)
            self.orionActiveAlertsObjs.append(thisObj)
        return self.orionActiveAlertsObjs

    def getOrionAlertDefinitions(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionAlertDefinitionsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'AlertDefID',
            'Name',
            'Description',
            'Enabled',
            'StartTime',
            'EndTime',
            'DOW',
            'TriggerQuery',
            'TriggerQueryDesign',
            'ResetQuery',
            'ResetQueryDesign',
            'SuppressionQuery',
            'SuppressionQueryDesign',
            'TriggerSustained',
            'ResetSustained',
            'LastExecuteTime',
            'ExecuteInterval',
            'BlockUntil',
            'ResponseTime',
            'LastErrorTime',
            'LastError',
            'ObjectType']
        tableName = 'Orion.AlertDefinitions'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionAlertDefinitions = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionAlertDefinitions is None:
                return []
        for obj in currOrionAlertDefinitions['results']:
            thisObj = OrionAlertDefinitions(connection=self, data=obj)
            self.orionAlertDefinitionsObjs.append(thisObj)
        return self.orionAlertDefinitionsObjs

    def getOrionAlerts(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionAlertsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'EngineID',
            'AlertID',
            'Name',
            'Enabled',
            'Description',
            'StartTime',
            'EndTime',
            'DOW',
            'NetObjects',
            'propertyID',
            'Trigger',
            'Reset',
            'Sustained',
            'TriggerSubjectTemplate',
            'TriggerMessageTemplate',
            'ResetSubjectTemplate',
            'ResetMessageTemplate',
            'Frequency',
            'EMailAddresses',
            'ReplyName',
            'ReplyAddress',
            'LogFile',
            'LogMessage',
            'ShellTrigger',
            'ShellReset',
            'SuppressionType',
            'Suppression']
        tableName = 'Orion.Alerts'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionAlerts = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionAlerts is None:
                return []
        for obj in currOrionAlerts['results']:
            thisObj = OrionAlerts(connection=self, data=obj)
            self.orionAlertsObjs.append(thisObj)
        return self.orionAlertsObjs

    def getOrionAlertStatus(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionAlertStatusObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'AlertDefID',
            'ActiveObject',
            'ObjectType',
            'State',
            'WorkingState',
            'ObjectName',
            'AlertMessage',
            'TriggerTimeStamp',
            'TriggerTimeOffset',
            'TriggerCount',
            'ResetTimeStamp',
            'Acknowledged',
            'AcknowledgedBy',
            'AcknowledgedTime',
            'LastUpdate',
            'AlertNotes',
            'Notes']
        tableName = 'Orion.AlertStatus'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionAlertStatus = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionAlertStatus is None:
                return []
        for obj in currOrionAlertStatus['results']:
            thisObj = OrionAlertStatus(connection=self, data=obj)
            self.orionAlertStatusObjs.append(thisObj)
        return self.orionAlertStatusObjs

    def getOrionAuditingActionTypes(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionAuditingActionTypesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = ['ActionTypeID', 'ActionType', 'ActionTypeDisplayName']
        tableName = 'Orion.AuditingActionTypes'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionAuditingActionTypes = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionAuditingActionTypes is None:
                return []
        for obj in currOrionAuditingActionTypes['results']:
            thisObj = OrionAuditingActionTypes(connection=self, data=obj)
            self.orionAuditingActionTypesObjs.append(thisObj)
        return self.orionAuditingActionTypesObjs

    def getOrionAuditingArguments(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionAuditingArgumentsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = ['AuditEventID', 'ArgsKey', 'ArgsValue']
        tableName = 'Orion.AuditingArguments'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionAuditingArguments = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionAuditingArguments is None:
                return []
        for obj in currOrionAuditingArguments['results']:
            thisObj = OrionAuditingArguments(connection=self, data=obj)
            self.orionAuditingArgumentsObjs.append(thisObj)
        return self.orionAuditingArgumentsObjs

    def getOrionAuditingEvents(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionAuditingEventsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'AuditEventID',
            'TimeLoggedUtc',
            'AccountID',
            'ActionTypeID',
            'AuditEventMessage',
            'NetworkNode',
            'NetObjectID',
            'NetObjectType']
        tableName = 'Orion.AuditingEvents'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionAuditingEvents = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionAuditingEvents is None:
                return []
        for obj in currOrionAuditingEvents['results']:
            thisObj = OrionAuditingEvents(connection=self, data=obj)
            self.orionAuditingEventsObjs.append(thisObj)
        return self.orionAuditingEventsObjs

    def getOrionContainer(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionContainerObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'ContainerID',
            'Name',
            'Owner',
            'Frequency',
            'StatusCalculator',
            'RollupType',
            'IsDeleted',
            'PollingEnabled',
            'LastChanged']
        tableName = 'Orion.Container'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionContainer = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionContainer is None:
                return []
        for obj in currOrionContainer['results']:
            thisObj = OrionContainer(connection=self, data=obj)
            self.orionContainerObjs.append(thisObj)
        return self.orionContainerObjs

    def getOrionContainerMemberDefinition(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionContainerMemberDefinitionObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'DefinitionID',
            'ContainerID',
            'Name',
            'Entity',
            'FromClause',
            'Expression',
            'Definition']
        tableName = 'Orion.ContainerMemberDefinition'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionContainerMemberDefinition = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionContainerMemberDefinition is None:
                return []
        for obj in currOrionContainerMemberDefinition['results']:
            thisObj = OrionContainerMemberDefinition(connection=self, data=obj)
            self.orionContainerMemberDefinitionObjs.append(thisObj)
        return self.orionContainerMemberDefinitionObjs

    def getOrionContainerMembers(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionContainerMembersObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'ContainerID',
            'MemberPrimaryID',
            'MemberEntityType',
            'Name',
            'Status',
            'MemberUri',
            'MemberAncestorDisplayNames',
            'MemberAncestorDetailsUrls']
        tableName = 'Orion.ContainerMembers'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionContainerMembers = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionContainerMembers is None:
                return []
        for obj in currOrionContainerMembers['results']:
            thisObj = OrionContainerMembers(connection=self, data=obj)
            self.orionContainerMembersObjs.append(thisObj)
        return self.orionContainerMembersObjs

    def getOrionContainerMemberSnapshots(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionContainerMemberSnapshotsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'ContainerMemberSnapshotID',
            'ContainerID',
            'Name',
            'FullName',
            'EntityDisplayName',
            'EntityDisplayNamePlural',
            'MemberUri',
            'Status']
        tableName = 'Orion.ContainerMemberSnapshots'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionContainerMemberSnapshots = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionContainerMemberSnapshots is None:
                return []
        for obj in currOrionContainerMemberSnapshots['results']:
            thisObj = OrionContainerMemberSnapshots(connection=self, data=obj)
            self.orionContainerMemberSnapshotsObjs.append(thisObj)
        return self.orionContainerMemberSnapshotsObjs

    def getOrionCPUMultiLoad(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionCPUMultiLoadObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'NodeID',
            'TimeStampUTC',
            'CPUIndex',
            'MinLoad',
            'MaxLoad',
            'AvgLoad']
        tableName = 'Orion.CPUMultiLoad'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionCPUMultiLoad = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionCPUMultiLoad is None:
                return []
        for obj in currOrionCPUMultiLoad['results']:
            thisObj = OrionCPUMultiLoad(connection=self, data=obj)
            self.orionCPUMultiLoadObjs.append(thisObj)
        return self.orionCPUMultiLoadObjs

    def getOrionCredential(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionCredentialObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'ID',
            'Name',
            'Description',
            'CredentialType',
            'CredentialOwner']
        tableName = 'Orion.Credential'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionCredential = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionCredential is None:
                return []
        for obj in currOrionCredential['results']:
            thisObj = OrionCredential(connection=self, data=obj)
            self.orionCredentialObjs.append(thisObj)
        return self.orionCredentialObjs

    def getOrionCustomProperty(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionCustomPropertyObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'Table',
            'Field',
            'DataType',
            'MaxLength',
            'StorageMethod',
            'Description',
            'TargetEntity']
        tableName = 'Orion.CustomProperty'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionCustomProperty = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionCustomProperty is None:
                return []
        for obj in currOrionCustomProperty['results']:
            thisObj = OrionCustomProperty(connection=self, data=obj)
            self.orionCustomPropertyObjs.append(thisObj)
        return self.orionCustomPropertyObjs

    def getOrionCustomPropertyUsage(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionCustomPropertyUsageObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'Table',
            'Field',
            'IsForAlerting',
            'IsForFiltering',
            'IsForGrouping',
            'IsForReporting',
            'IsForEntityDetail']
        tableName = 'Orion.CustomPropertyUsage'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionCustomPropertyUsage = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionCustomPropertyUsage is None:
                return []
        for obj in currOrionCustomPropertyUsage['results']:
            thisObj = OrionCustomPropertyUsage(connection=self, data=obj)
            self.orionCustomPropertyUsageObjs.append(thisObj)
        return self.orionCustomPropertyUsageObjs

    def getOrionCustomPropertyValues(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionCustomPropertyValuesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = ['Table', 'Field', 'Value']
        tableName = 'Orion.CustomPropertyValues'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionCustomPropertyValues = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionCustomPropertyValues is None:
                return []
        for obj in currOrionCustomPropertyValues['results']:
            thisObj = OrionCustomPropertyValues(connection=self, data=obj)
            self.orionCustomPropertyValuesObjs.append(thisObj)
        return self.orionCustomPropertyValuesObjs

    def getOrionDependencies(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionDependenciesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'DependencyId',
            'Name',
            'ParentUri',
            'ChildUri',
            'LastUpdateUTC']
        tableName = 'Orion.Dependencies'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionDependencies = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionDependencies is None:
                return []
        for obj in currOrionDependencies['results']:
            thisObj = OrionDependencies(connection=self, data=obj)
            self.orionDependenciesObjs.append(thisObj)
        return self.orionDependenciesObjs

    def getOrionDependencyEntities(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionDependencyEntitiesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = ['EntityName', 'ValidParent', 'ValidChild']
        tableName = 'Orion.DependencyEntities'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionDependencyEntities = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionDependencyEntities is None:
                return []
        for obj in currOrionDependencyEntities['results']:
            thisObj = OrionDependencyEntities(connection=self, data=obj)
            self.orionDependencyEntitiesObjs.append(thisObj)
        return self.orionDependencyEntitiesObjs

    def getOrionDiscoveredNodes(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionDiscoveredNodesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'NodeID',
            'ProfileID',
            'IPAddress',
            'IPAddressGUID',
            'SnmpVersion',
            'SubType',
            'CredentialID',
            'Hostname',
            'DNS',
            'SysObjectID',
            'Vendor',
            'VendorIcon',
            'MachineType',
            'SysDescription',
            'SysName',
            'Location',
            'Contact',
            'IgnoredNodeID']
        tableName = 'Orion.DiscoveredNodes'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionDiscoveredNodes = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionDiscoveredNodes is None:
                return []
        for obj in currOrionDiscoveredNodes['results']:
            thisObj = OrionDiscoveredNodes(connection=self, data=obj)
            self.orionDiscoveredNodesObjs.append(thisObj)
        return self.orionDiscoveredNodesObjs

    def getOrionDiscoveredPollers(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionDiscoveredPollersObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'ID',
            'ProfileID',
            'NetObjectID',
            'NetObjectType',
            'PollerType']
        tableName = 'Orion.DiscoveredPollers'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionDiscoveredPollers = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionDiscoveredPollers is None:
                return []
        for obj in currOrionDiscoveredPollers['results']:
            thisObj = OrionDiscoveredPollers(connection=self, data=obj)
            self.orionDiscoveredPollersObjs.append(thisObj)
        return self.orionDiscoveredPollersObjs

    def getOrionDiscoveredVolumes(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionDiscoveredVolumesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'ProfileID',
            'DiscoveredNodeID',
            'VolumeIndex',
            'VolumeType',
            'VolumeDescription',
            'IgnoredVolumeID']
        tableName = 'Orion.DiscoveredVolumes'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionDiscoveredVolumes = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionDiscoveredVolumes is None:
                return []
        for obj in currOrionDiscoveredVolumes['results']:
            thisObj = OrionDiscoveredVolumes(connection=self, data=obj)
            self.orionDiscoveredVolumesObjs.append(thisObj)
        return self.orionDiscoveredVolumesObjs

    def getOrionDiscoveryProfiles(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionDiscoveryProfilesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'ProfileID',
            'Name',
            'Description',
            'RunTimeInSeconds',
            'LastRun',
            'EngineID',
            'Status',
            'JobID',
            'SIPPort',
            'HopCount',
            'SearchTimeout',
            'SNMPTimeout',
            'SNMPRetries',
            'RepeatInterval',
            'Active',
            'DuplicateNodes',
            'ImportUpInterface',
            'ImportDownInterface',
            'ImportShutdownInterface',
            'SelectionMethod',
            'JobTimeout',
            'ScheduleRunAtTime',
            'ScheduleRunFrequency',
            'StatusDescription',
            'IsHidden',
            'IsAutoImport']
        tableName = 'Orion.DiscoveryProfiles'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionDiscoveryProfiles = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionDiscoveryProfiles is None:
                return []
        for obj in currOrionDiscoveryProfiles['results']:
            thisObj = OrionDiscoveryProfiles(connection=self, data=obj)
            self.orionDiscoveryProfilesObjs.append(thisObj)
        return self.orionDiscoveryProfilesObjs

    def getOrionElementInfo(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionElementInfoObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = ['ElementType', 'MaxElementCount']
        tableName = 'Orion.ElementInfo'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionElementInfo = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionElementInfo is None:
                return []
        for obj in currOrionElementInfo['results']:
            thisObj = OrionElementInfo(connection=self, data=obj)
            self.orionElementInfoObjs.append(thisObj)
        return self.orionElementInfoObjs

    def getOrionEvents(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionEventsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'EventID',
            'EventTime',
            'NetworkNode',
            'NetObjectID',
            'EventType',
            'Message',
            'Acknowledged',
            'NetObjectType',
            'TimeStamp']
        tableName = 'Orion.Events'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionEvents = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionEvents is None:
                return []
        for obj in currOrionEvents['results']:
            thisObj = OrionEvents(connection=self, data=obj)
            self.orionEventsObjs.append(thisObj)
        return self.orionEventsObjs

    def getOrionEventTypes(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionEventTypesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'EventType',
            'Name',
            'Bold',
            'BackColor',
            'Icon',
            'Sort',
            'Notify',
            'Record',
            'Sound',
            'Mute',
            'NotifyMessage',
            'NotifySubject']
        tableName = 'Orion.EventTypes'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionEventTypes = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionEventTypes is None:
                return []
        for obj in currOrionEventTypes['results']:
            thisObj = OrionEventTypes(connection=self, data=obj)
            self.orionEventTypesObjs.append(thisObj)
        return self.orionEventTypesObjs

    def getOrionNodeIPAddresses(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionNodeIPAddressesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'NodeID',
            'IPAddress',
            'IPAddressN',
            'IPAddressType',
            'InterfaceIndex']
        tableName = 'Orion.NodeIPAddresses'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionNodeIPAddresses = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionNodeIPAddresses is None:
                return []
        for obj in currOrionNodeIPAddresses['results']:
            thisObj = OrionNodeIPAddresses(connection=self, data=obj)
            self.orionNodeIPAddressesObjs.append(thisObj)
        return self.orionNodeIPAddressesObjs

    def getOrionNodeL2Connections(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionNodeL2ConnectionsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = ['NodeID', 'PortID', 'MACAddress', 'Status', 'VlanId']
        tableName = 'Orion.NodeL2Connections'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionNodeL2Connections = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionNodeL2Connections is None:
                return []
        for obj in currOrionNodeL2Connections['results']:
            thisObj = OrionNodeL2Connections(connection=self, data=obj)
            self.orionNodeL2ConnectionsObjs.append(thisObj)
        return self.orionNodeL2ConnectionsObjs

    def getOrionNodeL3Entries(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionNodeL3EntriesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = ['NodeID', 'IfIndex', 'MACAddress', 'IPAddress', 'Type']
        tableName = 'Orion.NodeL3Entries'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionNodeL3Entries = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionNodeL3Entries is None:
                return []
        for obj in currOrionNodeL3Entries['results']:
            thisObj = OrionNodeL3Entries(connection=self, data=obj)
            self.orionNodeL3EntriesObjs.append(thisObj)
        return self.orionNodeL3EntriesObjs

    def getOrionNodeLldpEntry(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionNodeLldpEntryObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'NodeID',
            'LocalPortNumber',
            'RemoteIfIndex',
            'RemotePortId',
            'RemotePortDescription',
            'RemoteSystemName',
            'RemoteIpAddress']
        tableName = 'Orion.NodeLldpEntry'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionNodeLldpEntry = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionNodeLldpEntry is None:
                return []
        for obj in currOrionNodeLldpEntry['results']:
            thisObj = OrionNodeLldpEntry(connection=self, data=obj)
            self.orionNodeLldpEntryObjs.append(thisObj)
        return self.orionNodeLldpEntryObjs

    def getOrionNodeMACAddresses(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionNodeMACAddressesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = ['NodeID', 'MAC', 'DateTime']
        tableName = 'Orion.NodeMACAddresses'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionNodeMACAddresses = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionNodeMACAddresses is None:
                return []
        for obj in currOrionNodeMACAddresses['results']:
            thisObj = OrionNodeMACAddresses(connection=self, data=obj)
            self.orionNodeMACAddressesObjs.append(thisObj)
        return self.orionNodeMACAddressesObjs

    def getOrionNodes(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionNodesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'NodeID', 'ObjectSubType', 'IPAddress', 'IPAddressType',
            'DynamicIP', 'Caption', 'NodeDescription', 'DNS', 'SysName',
            'Vendor', 'SysObjectID', 'Location', 'Contact', 'VendorIcon',
            'Icon', 'IOSImage', 'IOSVersion', 'GroupStatus', 'StatusIcon',
            'LastBoot', 'SystemUpTime', 'ResponseTime', 'PercentLoss',
            'AvgResponseTime', 'MinResponseTime', 'MaxResponseTime', 'CPULoad',
            'MemoryUsed', 'PercentMemoryUsed', 'LastSync',
            'LastSystemUpTimePollUtc', 'MachineType', 'Severity',
            'ChildStatus', 'Allow64BitCounters', 'AgentPort', 'TotalMemory',
            'CMTS', 'CustomPollerLastStatisticsPoll',
            'CustomPollerLastStatisticsPollSuccess', 'SNMPVersion',
            'PollInterval', 'EngineID', 'RediscoveryInterval', 'NextPoll',
            'NextRediscovery', 'StatCollection', 'External', 'Community',
            'RWCommunity', 'IP', 'IP_Address', 'IPAddressGUID', 'NodeName',
            'BlockUntil', 'BufferNoMemThisHour', 'BufferNoMemToday',
            'BufferSmMissThisHour', 'BufferSmMissToday',
            'BufferMdMissThisHour', 'BufferMdMissToday',
            'BufferBgMissThisHour', 'BufferBgMissToday',
            'BufferLgMissThisHour', 'BufferLgMissToday',
            'BufferHgMissThisHour', 'BufferHgMissToday', 'OrionIdPrefix',
            'OrionIdColumn']
        tableName = 'Orion.Nodes'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionNodes = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionNodes is None:
                return []
        for obj in currOrionNodes['results']:
            thisObj = OrionNodes(connection=self, data=obj)
            self.orionNodesObjs.append(thisObj)
        return self.orionNodesObjs

    def getOrionNodesCustomProperties(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionNodesCustomPropertiesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = ['NodeID', 'City', 'Comments', 'Department']
        tableName = 'Orion.NodesCustomProperties'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionNodesCustomProperties = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionNodesCustomProperties is None:
                return []
        for obj in currOrionNodesCustomProperties['results']:
            thisObj = OrionNodesCustomProperties(connection=self, data=obj)
            self.orionNodesCustomPropertiesObjs.append(thisObj)
        return self.orionNodesCustomPropertiesObjs

    def getOrionNodesStats(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionNodesStatsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'AvgResponseTime',
            'MinResponseTime',
            'MaxResponseTime',
            'ResponseTime',
            'PercentLoss',
            'CPULoad',
            'MemoryUsed',
            'PercentMemoryUsed',
            'LastBoot',
            'SystemUpTime',
            'NodeID']
        tableName = 'Orion.NodesStats'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionNodesStats = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionNodesStats is None:
                return []
        for obj in currOrionNodesStats['results']:
            thisObj = OrionNodesStats(connection=self, data=obj)
            self.orionNodesStatsObjs.append(thisObj)
        return self.orionNodesStatsObjs

    def getOrionNodeVlans(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionNodeVlansObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = ['NodeID', 'VlanId']
        tableName = 'Orion.NodeVlans'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionNodeVlans = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionNodeVlans is None:
                return []
        for obj in currOrionNodeVlans['results']:
            thisObj = OrionNodeVlans(connection=self, data=obj)
            self.orionNodeVlansObjs.append(thisObj)
        return self.orionNodeVlansObjs

    def getOrionNPMDiscoveredInterfaces(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionNPMDiscoveredInterfacesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'ProfileID',
            'DiscoveredNodeID',
            'DiscoveredInterfaceID',
            'InterfaceIndex',
            'InterfaceName',
            'InterfaceType',
            'InterfaceSubType',
            'InterfaceTypeDescription',
            'OperStatus',
            'AdminStatus',
            'PhysicalAddress',
            'IfName',
            'InterfaceAlias',
            'InterfaceTypeName',
            'IgnoredInterfaceID']
        tableName = 'Orion.NPM.DiscoveredInterfaces'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionNPMDiscoveredInterfaces = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionNPMDiscoveredInterfaces is None:
                return []
        for obj in currOrionNPMDiscoveredInterfaces['results']:
            thisObj = OrionNPMDiscoveredInterfaces(connection=self, data=obj)
            self.orionNPMDiscoveredInterfacesObjs.append(thisObj)
        return self.orionNPMDiscoveredInterfacesObjs

    def getOrionNPMInterfaceAvailability(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionNPMInterfaceAvailabilityObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'DateTime',
            'InterfaceID',
            'NodeID',
            'Availability',
            'Weight']
        tableName = 'Orion.NPM.InterfaceAvailability'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionNPMInterfaceAvailability = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionNPMInterfaceAvailability is None:
                return []
        for obj in currOrionNPMInterfaceAvailability['results']:
            thisObj = OrionNPMInterfaceAvailability(connection=self, data=obj)
            self.orionNPMInterfaceAvailabilityObjs.append(thisObj)
        return self.orionNPMInterfaceAvailabilityObjs

    def getOrionNPMInterfaceErrors(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionNPMInterfaceErrorsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'NodeID',
            'InterfaceID',
            'DateTime',
            'Archive',
            'InErrors',
            'InDiscards',
            'OutErrors',
            'OutDiscards']
        tableName = 'Orion.NPM.InterfaceErrors'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionNPMInterfaceErrors = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionNPMInterfaceErrors is None:
                return []
        for obj in currOrionNPMInterfaceErrors['results']:
            thisObj = OrionNPMInterfaceErrors(connection=self, data=obj)
            self.orionNPMInterfaceErrorsObjs.append(thisObj)
        return self.orionNPMInterfaceErrorsObjs

    def getOrionNPMInterfaces(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionNPMInterfacesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'NodeID', 'InterfaceID', 'ObjectSubType', 'Name', 'Index', 'Icon',
            'Type', 'TypeName', 'TypeDescription', 'Speed', 'MTU',
            'LastChange', 'PhysicalAddress', 'AdminStatus', 'OperStatus',
            'StatusIcon', 'InBandwidth', 'OutBandwidth', 'Caption', 'FullName',
            'Outbps', 'Inbps', 'OutPercentUtil', 'InPercentUtil', 'OutPps',
            'InPps', 'InPktSize', 'OutPktSize', 'OutUcastPps', 'OutMcastPps',
            'InUcastPps', 'InMcastPps', 'InDiscardsThisHour',
            'InDiscardsToday', 'InErrorsThisHour', 'InErrorsToday',
            'OutDiscardsThisHour', 'OutDiscardsToday', 'OutErrorsThisHour',
            'OutErrorsToday', 'MaxInBpsToday', 'MaxInBpsTime',
            'MaxOutBpsToday', 'MaxOutBpsTime', 'Counter64', 'LastSync',
            'Alias', 'IfName', 'Severity', 'CustomBandwidth',
            'CustomPollerLastStatisticsPoll', 'PollInterval', 'NextPoll',
            'RediscoveryInterval', 'NextRediscovery', 'StatCollection',
            'UnPluggable', 'InterfaceSpeed', 'InterfaceCaption',
            'InterfaceType', 'InterfaceSubType', 'MAC', 'InterfaceName',
            'InterfaceIcon', 'InterfaceTypeName', 'AdminStatusLED',
            'OperStatusLED', 'InterfaceAlias', 'InterfaceIndex',
            'InterfaceLastChange', 'InterfaceMTU', 'InterfaceTypeDescription',
            'OrionIdPrefix', 'OrionIdColumn']
        tableName = 'Orion.NPM.Interfaces'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionNPMInterfaces = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionNPMInterfaces is None:
                return []
        for obj in currOrionNPMInterfaces['results']:
            thisObj = OrionNPMInterfaces(connection=self, data=obj)
            self.orionNPMInterfacesObjs.append(thisObj)
        return self.orionNPMInterfacesObjs

    def getOrionNPMInterfaceTraffic(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionNPMInterfaceTrafficObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'NodeID',
            'InterfaceID',
            'DateTime',
            'Archive',
            'InAveragebps',
            'InMinbps',
            'InMaxbps',
            'InTotalBytes',
            'InTotalPkts',
            'InAvgUniCastPkts',
            'InMinUniCastPkts',
            'InMaxUniCastPkts',
            'InAvgMultiCastPkts',
            'InMinMultiCastPkts',
            'InMaxMultiCastPkts',
            'OutAveragebps',
            'OutMinbps',
            'OutMaxbps',
            'OutTotalBytes',
            'OutTotalPkts',
            'OutAvgUniCastPkts',
            'OutMaxUniCastPkts',
            'OutMinUniCastPkts',
            'OutAvgMultiCastPkts',
            'OutMinMultiCastPkts',
            'OutMaxMultiCastPkts']
        tableName = 'Orion.NPM.InterfaceTraffic'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionNPMInterfaceTraffic = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionNPMInterfaceTraffic is None:
                return []
        for obj in currOrionNPMInterfaceTraffic['results']:
            thisObj = OrionNPMInterfaceTraffic(connection=self, data=obj)
            self.orionNPMInterfaceTrafficObjs.append(thisObj)
        return self.orionNPMInterfaceTrafficObjs

    def getOrionPollers(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionPollersObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'PollerID',
            'PollerType',
            'NetObject',
            'NetObjectType',
            'NetObjectID',
            'Enabled']
        tableName = 'Orion.Pollers'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionPollers = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionPollers is None:
                return []
        for obj in currOrionPollers['results']:
            thisObj = OrionPollers(connection=self, data=obj)
            self.orionPollersObjs.append(thisObj)
        return self.orionPollersObjs

    def getOrionReport(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionReportObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'ReportID',
            'Name',
            'Category',
            'Title',
            'Type',
            'SubTitle',
            'Description',
            'LegacyPath',
            'Definition',
            'ModuleTitle',
            'RecipientList',
            'LimitationCategory',
            'Owner',
            'LastRenderDuration']
        tableName = 'Orion.Report'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionReport = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionReport is None:
                return []
        for obj in currOrionReport['results']:
            thisObj = OrionReport(connection=self, data=obj)
            self.orionReportObjs.append(thisObj)
        return self.orionReportObjs

    def getOrionResponseTime(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionResponseTimeObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'NodeID',
            'DateTime',
            'Archive',
            'AvgResponseTime',
            'MinResponseTime',
            'MaxResponseTime',
            'PercentLoss',
            'Availability']
        tableName = 'Orion.ResponseTime'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionResponseTime = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionResponseTime is None:
                return []
        for obj in currOrionResponseTime['results']:
            thisObj = OrionResponseTime(connection=self, data=obj)
            self.orionResponseTimeObjs.append(thisObj)
        return self.orionResponseTimeObjs

    def getOrionServices(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionServicesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = ['DisplayName', 'ServiceName', 'Status', 'Memory']
        tableName = 'Orion.Services'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionServices = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionServices is None:
                return []
        for obj in currOrionServices['results']:
            thisObj = OrionServices(connection=self, data=obj)
            self.orionServicesObjs.append(thisObj)
        return self.orionServicesObjs

    def getOrionSysLog(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionSysLogObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'MessageID',
            'EngineID',
            'DateTime',
            'IPAddress',
            'Acknowledged',
            'SysLogFacility',
            'SysLogSeverity',
            'Hostname',
            'MessageType',
            'Message',
            'SysLogTag',
            'FirstIPInMessage',
            'SecIPInMessage',
            'MacInMessage',
            'TimeStamp',
            'NodeID']
        tableName = 'Orion.SysLog'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionSysLog = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionSysLog is None:
                return []
        for obj in currOrionSysLog['results']:
            thisObj = OrionSysLog(connection=self, data=obj)
            self.orionSysLogObjs.append(thisObj)
        return self.orionSysLogObjs

    def getOrionTopologyData(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionTopologyDataObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'DiscoveryProfileID',
            'SrcNodeID',
            'SrcInterfaceID',
            'DestNodeID',
            'DestInterfaceID',
            'SrcType',
            'DestType',
            'DataSourceNodeID',
            'LastUpdateUtc']
        tableName = 'Orion.TopologyData'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionTopologyData = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionTopologyData is None:
                return []
        for obj in currOrionTopologyData['results']:
            thisObj = OrionTopologyData(connection=self, data=obj)
            self.orionTopologyDataObjs.append(thisObj)
        return self.orionTopologyDataObjs

    def getOrionTraps(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionTrapsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'TrapID',
            'EngineID',
            'DateTime',
            'IPAddress',
            'Community',
            'Tag',
            'Acknowledged',
            'Hostname',
            'NodeID',
            'TrapType',
            'ColorCode',
            'TimeStamp']
        tableName = 'Orion.Traps'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionTraps = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionTraps is None:
                return []
        for obj in currOrionTraps['results']:
            thisObj = OrionTraps(connection=self, data=obj)
            self.orionTrapsObjs.append(thisObj)
        return self.orionTrapsObjs

    def getOrionViews(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionViewsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'ViewID',
            'ViewKey',
            'ViewTitle',
            'ViewType',
            'Columns',
            'Column1Width',
            'Column2Width',
            'Column3Width',
            'System',
            'Customizable',
            'LimitationID']
        tableName = 'Orion.Views'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionViews = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionViews is None:
                return []
        for obj in currOrionViews['results']:
            thisObj = OrionViews(connection=self, data=obj)
            self.orionViewsObjs.append(thisObj)
        return self.orionViewsObjs

    def getOrionVIMClusters(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionVIMClustersObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'ClusterID',
            'ManagedObjectID',
            'DataCenterID',
            'Name',
            'TotalMemory',
            'TotalCpu',
            'CpuCoreCount',
            'CpuThreadCount',
            'EffectiveCpu',
            'EffectiveMemory',
            'DrsBehaviour',
            'DrsStatus',
            'DrsVmotionRate',
            'HaAdmissionControlStatus',
            'HaStatus',
            'HaFailoverLevel',
            'ConfigStatus',
            'OverallStatus',
            'CPULoad',
            'CPUUsageMHz',
            'MemoryUsage',
            'MemoryUsageMB']
        tableName = 'Orion.VIM.Clusters'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionVIMClusters = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionVIMClusters is None:
                return []
        for obj in currOrionVIMClusters['results']:
            thisObj = OrionVIMClusters(connection=self, data=obj)
            self.orionVIMClustersObjs.append(thisObj)
        return self.orionVIMClustersObjs

    def getOrionVIMClusterStatistics(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionVIMClusterStatisticsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'ClusterID',
            'DateTime',
            'PercentAvailability',
            'MinCPULoad',
            'MaxCPULoad',
            'AvgCPULoad',
            'MinCPUUsageMHz',
            'MaxCPUUsageMHz',
            'AvgCPUUsageMHz',
            'MinMemoryUsage',
            'MaxMemoryUsage',
            'AvgMemoryUsage',
            'MinMemoryUsageMB',
            'MaxMemoryUsageMB',
            'AvgMemoryUsageMB']
        tableName = 'Orion.VIM.ClusterStatistics'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionVIMClusterStatistics = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionVIMClusterStatistics is None:
                return []
        for obj in currOrionVIMClusterStatistics['results']:
            thisObj = OrionVIMClusterStatistics(connection=self, data=obj)
            self.orionVIMClusterStatisticsObjs.append(thisObj)
        return self.orionVIMClusterStatisticsObjs

    def getOrionVIMDataCenters(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionVIMDataCentersObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'DataCenterID',
            'ManagedObjectID',
            'VCenterID',
            'Name',
            'ConfigStatus',
            'OverallStatus',
            'ManagedStatus']
        tableName = 'Orion.VIM.DataCenters'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionVIMDataCenters = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionVIMDataCenters is None:
                return []
        for obj in currOrionVIMDataCenters['results']:
            thisObj = OrionVIMDataCenters(connection=self, data=obj)
            self.orionVIMDataCentersObjs.append(thisObj)
        return self.orionVIMDataCentersObjs

    def getOrionVIMHostIPAddresses(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionVIMHostIPAddressesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = ['HostID', 'IPAddress']
        tableName = 'Orion.VIM.HostIPAddresses'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionVIMHostIPAddresses = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionVIMHostIPAddresses is None:
                return []
        for obj in currOrionVIMHostIPAddresses['results']:
            thisObj = OrionVIMHostIPAddresses(connection=self, data=obj)
            self.orionVIMHostIPAddressesObjs.append(thisObj)
        return self.orionVIMHostIPAddressesObjs

    def getOrionVIMHosts(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionVIMHostsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'HostID',
            'ManagedObjectID',
            'NodeID',
            'HostName',
            'ClusterID',
            'DataCenterID',
            'VMwareProductName',
            'VMwareProductVersion',
            'PollingJobID',
            'ServiceURIID',
            'CredentialID',
            'HostStatus',
            'PollingMethod',
            'Model',
            'Vendor',
            'ProcessorType',
            'CpuCoreCount',
            'CpuPkgCount',
            'CpuMhz',
            'NicCount',
            'HbaCount',
            'HbaFcCount',
            'HbaScsiCount',
            'HbaIscsiCount',
            'MemorySize',
            'BuildNumber',
            'BiosSerial',
            'IPAddress',
            'ConnectionState',
            'ConfigStatus',
            'OverallStatus',
            'NodeStatus',
            'NetworkUtilization',
            'NetworkUsageRate',
            'NetworkTransmitRate',
            'NetworkReceiveRate',
            'NetworkCapacityKbps',
            'CpuLoad',
            'CpuUsageMHz',
            'MemUsage',
            'MemUsageMB',
            'VmCount',
            'VmRunningCount',
            'StatusMessage',
            'PlatformID']
        tableName = 'Orion.VIM.Hosts'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionVIMHosts = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionVIMHosts is None:
                return []
        for obj in currOrionVIMHosts['results']:
            thisObj = OrionVIMHosts(connection=self, data=obj)
            self.orionVIMHostsObjs.append(thisObj)
        return self.orionVIMHostsObjs

    def getOrionVIMHostStatistics(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionVIMHostStatisticsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'HostID',
            'DateTime',
            'VmCount',
            'VmRunningCount',
            'MinNetworkUtilization',
            'MaxNetworkUtilization',
            'AvgNetworkUtilization',
            'MinNetworkUsageRate',
            'MaxNetworkUsageRate',
            'AvgNetworkUsageRate',
            'MinNetworkTransmitRate',
            'MaxNetworkTransmitRate',
            'AvgNetworkTransmitRate',
            'MinNetworkReceiveRate',
            'MaxNetworkReceiveRate',
            'AvgNetworkReceiveRate']
        tableName = 'Orion.VIM.HostStatistics'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionVIMHostStatistics = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionVIMHostStatistics is None:
                return []
        for obj in currOrionVIMHostStatistics['results']:
            thisObj = OrionVIMHostStatistics(connection=self, data=obj)
            self.orionVIMHostStatisticsObjs.append(thisObj)
        return self.orionVIMHostStatisticsObjs

    def getOrionVIMManagedEntity(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionVIMManagedEntityObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'Status',
            'StatusDescription',
            'StatusLED',
            'UnManaged',
            'UnManageFrom',
            'UnManageUntil',
            'TriggeredAlarmDescription',
            'DetailsUrl',
            'Image']
        tableName = 'Orion.VIM.ManagedEntity'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionVIMManagedEntity = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionVIMManagedEntity is None:
                return []
        for obj in currOrionVIMManagedEntity['results']:
            thisObj = OrionVIMManagedEntity(connection=self, data=obj)
            self.orionVIMManagedEntityObjs.append(thisObj)
        return self.orionVIMManagedEntityObjs

    def getOrionVIMResourcePools(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionVIMResourcePoolsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'ResourcePoolID',
            'ManagedObjectID',
            'Name',
            'CpuMaxUsage',
            'CpuOverallUsage',
            'CpuReservationUsedForVM',
            'CpuReservationUsed',
            'MemMaxUsage',
            'MemOverallUsage',
            'MemReservationUsedForVM',
            'MemReservationUsed',
            'LastModifiedTime',
            'CpuExpandable',
            'CpuLimit',
            'CpuReservation',
            'CpuShareLevel',
            'CpuShareCount',
            'MemExpandable',
            'MemLimit',
            'MemReservation',
            'MemShareLevel',
            'MemShareCount',
            'ConfigStatus',
            'OverallStatus',
            'ManagedStatus',
            'ClusterID',
            'VCenterID',
            'ParentResourcePoolID']
        tableName = 'Orion.VIM.ResourcePools'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionVIMResourcePools = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionVIMResourcePools is None:
                return []
        for obj in currOrionVIMResourcePools['results']:
            thisObj = OrionVIMResourcePools(connection=self, data=obj)
            self.orionVIMResourcePoolsObjs.append(thisObj)
        return self.orionVIMResourcePoolsObjs

    def getOrionVIMThresholds(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionVIMThresholdsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = ['ThresholdID', 'TypeID', 'Warning', 'High', 'Maximum']
        tableName = 'Orion.VIM.Thresholds'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionVIMThresholds = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionVIMThresholds is None:
                return []
        for obj in currOrionVIMThresholds['results']:
            thisObj = OrionVIMThresholds(connection=self, data=obj)
            self.orionVIMThresholdsObjs.append(thisObj)
        return self.orionVIMThresholdsObjs

    def getOrionVIMThresholdTypes(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionVIMThresholdTypesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'TypeID',
            'Name',
            'Information',
            'Warning',
            'High',
            'Maximum']
        tableName = 'Orion.VIM.ThresholdTypes'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionVIMThresholdTypes = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionVIMThresholdTypes is None:
                return []
        for obj in currOrionVIMThresholdTypes['results']:
            thisObj = OrionVIMThresholdTypes(connection=self, data=obj)
            self.orionVIMThresholdTypesObjs.append(thisObj)
        return self.orionVIMThresholdTypesObjs

    def getOrionVIMVCenters(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionVIMVCentersObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'VCenterID',
            'NodeID',
            'Name',
            'VMwareProductName',
            'VMwareProductVersion',
            'PollingJobID',
            'ServiceURIID',
            'CredentialID',
            'HostStatus',
            'Model',
            'Vendor',
            'BuildNumber',
            'BiosSerial',
            'IPAddress',
            'ConnectionState',
            'StatusMessage']
        tableName = 'Orion.VIM.VCenters'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionVIMVCenters = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionVIMVCenters is None:
                return []
        for obj in currOrionVIMVCenters['results']:
            thisObj = OrionVIMVCenters(connection=self, data=obj)
            self.orionVIMVCentersObjs.append(thisObj)
        return self.orionVIMVCentersObjs

    def getOrionVIMVirtualMachines(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionVIMVirtualMachinesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'VirtualMachineID',
            'ManagedObjectID',
            'UUID',
            'HostID',
            'NodeID',
            'ResourcePoolID',
            'VMConfigFile',
            'MemoryConfigured',
            'MemoryShares',
            'CPUShares',
            'GuestState',
            'IPAddress',
            'LogDirectory',
            'GuestVmWareToolsVersion',
            'GuestVmWareToolsStatus',
            'Name',
            'GuestName',
            'GuestFamily',
            'GuestDnsName',
            'NicCount',
            'VDisksCount',
            'ProcessorCount',
            'PowerState',
            'BootTime',
            'ConfigStatus',
            'OverallStatus',
            'NodeStatus',
            'NetworkUsageRate',
            'NetworkTransmitRate',
            'NetworkReceiveRate',
            'CpuLoad',
            'CpuUsageMHz',
            'MemUsage',
            'MemUsageMB',
            'IsLicensed']
        tableName = 'Orion.VIM.VirtualMachines'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionVIMVirtualMachines = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionVIMVirtualMachines is None:
                return []
        for obj in currOrionVIMVirtualMachines['results']:
            thisObj = OrionVIMVirtualMachines(connection=self, data=obj)
            self.orionVIMVirtualMachinesObjs.append(thisObj)
        return self.orionVIMVirtualMachinesObjs

    def getOrionVIMVMStatistics(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionVIMVMStatisticsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'VirtualMachineID',
            'DateTime',
            'MinCPULoad',
            'MaxCPULoad',
            'AvgCPULoad',
            'MinMemoryUsage',
            'MaxMemoryUsage',
            'AvgMemoryUsage',
            'MinNetworkUsageRate',
            'MaxNetworkUsageRate',
            'AvgNetworkUsageRate',
            'MinNetworkTransmitRate',
            'MaxNetworkTransmitRate',
            'AvgNetworkTransmitRate',
            'MinNetworkReceiveRate',
            'MaxNetworkReceiveRate',
            'AvgNetworkReceiveRate',
            'Availability']
        tableName = 'Orion.VIM.VMStatistics'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionVIMVMStatistics = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionVIMVMStatistics is None:
                return []
        for obj in currOrionVIMVMStatistics['results']:
            thisObj = OrionVIMVMStatistics(connection=self, data=obj)
            self.orionVIMVMStatisticsObjs.append(thisObj)
        return self.orionVIMVMStatisticsObjs

    def getOrionVolumePerformanceHistory(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionVolumePerformanceHistoryObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'NodeID',
            'VolumeID',
            'DateTime',
            'AvgDiskQueueLength',
            'MinDiskQueueLength',
            'MaxDiskQueueLength',
            'AvgDiskTransfer',
            'MinDiskTransfer',
            'MaxDiskTransfer',
            'AvgDiskReads',
            'MinDiskReads',
            'MaxDiskReads',
            'AvgDiskWrites',
            'MinDiskWrites',
            'MaxDiskWrites']
        tableName = 'Orion.VolumePerformanceHistory'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionVolumePerformanceHistory = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionVolumePerformanceHistory is None:
                return []
        for obj in currOrionVolumePerformanceHistory['results']:
            thisObj = OrionVolumePerformanceHistory(connection=self, data=obj)
            self.orionVolumePerformanceHistoryObjs.append(thisObj)
        return self.orionVolumePerformanceHistoryObjs

    def getOrionVolumes(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionVolumesObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'NodeID',
            'VolumeID',
            'Icon',
            'Index',
            'Caption',
            'PollInterval',
            'StatCollection',
            'RediscoveryInterval',
            'StatusIcon',
            'Type',
            'Size',
            'Responding',
            'FullName',
            'LastSync',
            'VolumePercentUsed',
            'VolumeAllocationFailuresThisHour',
            'VolumeIndex',
            'VolumeType',
            'VolumeDescription',
            'VolumeSize',
            'VolumeSpaceUsed',
            'VolumeAllocationFailuresToday',
            'VolumeResponding',
            'VolumeSpaceAvailable',
            'VolumeTypeIcon',
            'OrionIdPrefix',
            'OrionIdColumn',
            'DiskQueueLength',
            'DiskTransfer',
            'DiskReads',
            'DiskWrites',
            'TotalDiskIOPS']
        tableName = 'Orion.Volumes'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionVolumes = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionVolumes is None:
                return []
        for obj in currOrionVolumes['results']:
            thisObj = OrionVolumes(connection=self, data=obj)
            self.orionVolumesObjs.append(thisObj)
        return self.orionVolumesObjs

    def getOrionVolumesStats(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionVolumesStatsObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'PercentUsed',
            'SpaceUsed',
            'SpaceAvailable',
            'AllocationFailuresThisHour',
            'AllocationFailuresToday',
            'DiskQueueLength',
            'DiskTransfer',
            'DiskReads',
            'DiskWrites',
            'TotalDiskIOPS',
            'VolumeID']
        tableName = 'Orion.VolumesStats'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionVolumesStats = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionVolumesStats is None:
                return []
        for obj in currOrionVolumesStats['results']:
            thisObj = OrionVolumesStats(connection=self, data=obj)
            self.orionVolumesStatsObjs.append(thisObj)
        return self.orionVolumesStatsObjs

    def getOrionVolumeUsageHistory(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['selectList', 'whereList']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        self.orionVolumeUsageHistoryObjs = []
        self.selectList = ar['selectList']
        self.whereList = ar['whereList']
        fieldList = [
            'NodeID',
            'VolumeID',
            'DateTime',
            'DiskSize',
            'AvgDiskUsed',
            'MinDiskUsed',
            'MaxDiskUsed',
            'PercentDiskUsed',
            'AllocationFailures']
        tableName = 'Orion.VolumeUsageHistory'
        selectQuery = None
        if not ar['selectList'] and not ar['whereList']:
            selectQuery = convertFieldListToSelect(fieldList, tableName)
        elif ar['selectList'] and not ar['whereList']:
            selectQuery = convertSelectListToSelect(
                fieldList,
                tableName,
                ar['selectList'])
        elif not ar['selectList'] and ar['whereList']:
            selectQuery = convertWhereListToWhere(
                fieldList,
                tableName,
                ar['whereList'])
        elif ar['selectList'] and ar['whereList']:
            selectQuery = convertSelectWhereListToSelectWhere(
                fieldList,
                tableName,
                ar['selectList'],
                ar['whereList'])
        if selectQuery:
            currOrionVolumeUsageHistory = self.sendRequest(
                Type='GET',
                URL='/SolarWinds/InformationService/v3/Json/Query?query=' +
                selectQuery,
                status=200)
            if currOrionVolumeUsageHistory is None:
                return []
        for obj in currOrionVolumeUsageHistory['results']:
            thisObj = OrionVolumeUsageHistory(connection=self, data=obj)
            self.orionVolumeUsageHistoryObjs.append(thisObj)
        return self.orionVolumeUsageHistoryObjs


class OrionAccounts():

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.accountID = data.get('AccountID')
        self.enabled = data.get('Enabled')
        self.allowNodeManagement = data.get('AllowNodeManagement')
        self.allowAdmin = data.get('AllowAdmin')
        self.canClearEvents = data.get('CanClearEvents')
        self.allowReportManagement = data.get('AllowReportManagement')
        self.expires = data.get('Expires')
        self.lastLogin = data.get('LastLogin')
        self.limitationID1 = data.get('LimitationID1')
        self.limitationID2 = data.get('LimitationID2')
        self.limitationID3 = data.get('LimitationID3')
        self.accountSID = data.get('AccountSID')
        self.accountType = data.get('AccountType')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.alertID = data.get('AlertID')
        self.alertTime = data.get('AlertTime')
        self.objectType = data.get('ObjectType')
        self.objectID = data.get('ObjectID')
        self.objectName = data.get('ObjectName')
        self.nodeID = data.get('NodeID')
        self.nodeName = data.get('NodeName')
        self.eventMessage = data.get('EventMessage')
        self.propertyID = data.get('propertyID')
        self.monitoredproperty = data.get('Monitoredproperty')
        self.currentValue = data.get('CurrentValue')
        self.triggerValue = data.get('TriggerValue')
        self.resetValue = data.get('ResetValue')
        self.engineID = data.get('EngineID')
        self.alertNotes = data.get('AlertNotes')
        self.expireTime = data.get('ExpireTime')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.alertDefID = data.get('AlertDefID')
        self.name = data.get('Name')
        self.description = data.get('Description')
        self.enabled = data.get('Enabled')
        self.startTime = data.get('StartTime')
        self.endTime = data.get('EndTime')
        self.dOW = data.get('DOW')
        self.triggerQuery = data.get('TriggerQuery')
        self.triggerQueryDesign = data.get('TriggerQueryDesign')
        self.resetQuery = data.get('ResetQuery')
        self.resetQueryDesign = data.get('ResetQueryDesign')
        self.suppressionQuery = data.get('SuppressionQuery')
        self.suppressionQueryDesign = data.get('SuppressionQueryDesign')
        self.triggerSustained = data.get('TriggerSustained')
        self.resetSustained = data.get('ResetSustained')
        self.lastExecuteTime = data.get('LastExecuteTime')
        self.executeInterval = data.get('ExecuteInterval')
        self.blockUntil = data.get('BlockUntil')
        self.responseTime = data.get('ResponseTime')
        self.lastErrorTime = data.get('LastErrorTime')
        self.lastError = data.get('LastError')
        self.objectType = data.get('ObjectType')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.engineID = data.get('EngineID')
        self.alertID = data.get('AlertID')
        self.name = data.get('Name')
        self.enabled = data.get('Enabled')
        self.description = data.get('Description')
        self.startTime = data.get('StartTime')
        self.endTime = data.get('EndTime')
        self.dOW = data.get('DOW')
        self.netObjects = data.get('NetObjects')
        self.propertyID = data.get('propertyID')
        self.trigger = data.get('Trigger')
        self.reset = data.get('Reset')
        self.sustained = data.get('Sustained')
        self.triggerSubjectTemplate = data.get('TriggerSubjectTemplate')
        self.triggerMessageTemplate = data.get('TriggerMessageTemplate')
        self.resetSubjectTemplate = data.get('ResetSubjectTemplate')
        self.resetMessageTemplate = data.get('ResetMessageTemplate')
        self.frequency = data.get('Frequency')
        self.eMailAddresses = data.get('EMailAddresses')
        self.replyName = data.get('ReplyName')
        self.replyAddress = data.get('ReplyAddress')
        self.logFile = data.get('LogFile')
        self.logMessage = data.get('LogMessage')
        self.shellTrigger = data.get('ShellTrigger')
        self.shellReset = data.get('ShellReset')
        self.suppressionType = data.get('SuppressionType')
        self.suppression = data.get('Suppression')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.alertDefID = data.get('AlertDefID')
        self.activeObject = data.get('ActiveObject')
        self.objectType = data.get('ObjectType')
        self.state = data.get('State')
        self.workingState = data.get('WorkingState')
        self.objectName = data.get('ObjectName')
        self.alertMessage = data.get('AlertMessage')
        self.triggerTimeStamp = data.get('TriggerTimeStamp')
        self.triggerTimeOffset = data.get('TriggerTimeOffset')
        self.triggerCount = data.get('TriggerCount')
        self.resetTimeStamp = data.get('ResetTimeStamp')
        self.acknowledged = data.get('Acknowledged')
        self.acknowledgedBy = data.get('AcknowledgedBy')
        self.acknowledgedTime = data.get('AcknowledgedTime')
        self.lastUpdate = data.get('LastUpdate')
        self.alertNotes = data.get('AlertNotes')
        self.notes = data.get('Notes')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.actionTypeID = data.get('ActionTypeID')
        self.actionType = data.get('ActionType')
        self.actionTypeDisplayName = data.get('ActionTypeDisplayName')

    def getActionTypeID(self):
        return self.actionTypeID

    def getActionType(self):
        return self.actionType

    def getActionTypeDisplayName(self):
        return self.actionTypeDisplayName


class OrionAuditingArguments():

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.auditEventID = data.get('AuditEventID')
        self.argsKey = data.get('ArgsKey')
        self.argsValue = data.get('ArgsValue')

    def getAuditEventID(self):
        return self.auditEventID

    def getArgsKey(self):
        return self.argsKey

    def getArgsValue(self):
        return self.argsValue


class OrionAuditingEvents():

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.auditEventID = data.get('AuditEventID')
        self.timeLoggedUtc = data.get('TimeLoggedUtc')
        self.accountID = data.get('AccountID')
        self.actionTypeID = data.get('ActionTypeID')
        self.auditEventMessage = data.get('AuditEventMessage')
        self.networkNode = data.get('NetworkNode')
        self.netObjectID = data.get('NetObjectID')
        self.netObjectType = data.get('NetObjectType')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.containerID = data.get('ContainerID')
        self.name = data.get('Name')
        self.owner = data.get('Owner')
        self.frequency = data.get('Frequency')
        self.statusCalculator = data.get('StatusCalculator')
        self.rollupType = data.get('RollupType')
        self.isDeleted = data.get('IsDeleted')
        self.pollingEnabled = data.get('PollingEnabled')
        self.lastChanged = data.get('LastChanged')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.definitionID = data.get('DefinitionID')
        self.containerID = data.get('ContainerID')
        self.name = data.get('Name')
        self.entity = data.get('Entity')
        self.fromClause = data.get('FromClause')
        self.expression = data.get('Expression')
        self.definition = data.get('Definition')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.containerID = data.get('ContainerID')
        self.memberPrimaryID = data.get('MemberPrimaryID')
        self.memberEntityType = data.get('MemberEntityType')
        self.name = data.get('Name')
        self.status = data.get('Status')
        self.memberUri = data.get('MemberUri')
        self.memberAncestorDisplayNames = data.get(
            'MemberAncestorDisplayNames')
        self.memberAncestorDetailsUrls = data.get('MemberAncestorDetailsUrls')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.containerMemberSnapshotID = data.get('ContainerMemberSnapshotID')
        self.containerID = data.get('ContainerID')
        self.name = data.get('Name')
        self.fullName = data.get('FullName')
        self.entityDisplayName = data.get('EntityDisplayName')
        self.entityDisplayNamePlural = data.get('EntityDisplayNamePlural')
        self.memberUri = data.get('MemberUri')
        self.status = data.get('Status')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.nodeID = data.get('NodeID')
        self.timeStampUTC = data.get('TimeStampUTC')
        self.cPUIndex = data.get('CPUIndex')
        self.minLoad = data.get('MinLoad')
        self.maxLoad = data.get('MaxLoad')
        self.avgLoad = data.get('AvgLoad')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.iD = data.get('ID')
        self.name = data.get('Name')
        self.description = data.get('Description')
        self.credentialType = data.get('CredentialType')
        self.credentialOwner = data.get('CredentialOwner')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.table = data.get('Table')
        self.field = data.get('Field')
        self.dataType = data.get('DataType')
        self.maxLength = data.get('MaxLength')
        self.storageMethod = data.get('StorageMethod')
        self.description = data.get('Description')
        self.targetEntity = data.get('TargetEntity')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.table = data.get('Table')
        self.field = data.get('Field')
        self.isForAlerting = data.get('IsForAlerting')
        self.isForFiltering = data.get('IsForFiltering')
        self.isForGrouping = data.get('IsForGrouping')
        self.isForReporting = data.get('IsForReporting')
        self.isForEntityDetail = data.get('IsForEntityDetail')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.table = data.get('Table')
        self.field = data.get('Field')
        self.value = data.get('Value')

    def getTable(self):
        return self.table

    def getField(self):
        return self.field

    def getValue(self):
        return self.value


class OrionDependencies():

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.dependencyId = data.get('DependencyId')
        self.name = data.get('Name')
        self.parentUri = data.get('ParentUri')
        self.childUri = data.get('ChildUri')
        self.lastUpdateUTC = data.get('LastUpdateUTC')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.entityName = data.get('EntityName')
        self.validParent = data.get('ValidParent')
        self.validChild = data.get('ValidChild')

    def getEntityName(self):
        return self.entityName

    def getValidParent(self):
        return self.validParent

    def getValidChild(self):
        return self.validChild


class OrionDiscoveredNodes():

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.nodeID = data.get('NodeID')
        self.profileID = data.get('ProfileID')
        self.iPAddress = data.get('IPAddress')
        self.iPAddressGUID = data.get('IPAddressGUID')
        self.snmpVersion = data.get('SnmpVersion')
        self.subType = data.get('SubType')
        self.credentialID = data.get('CredentialID')
        self.hostname = data.get('Hostname')
        self.dNS = data.get('DNS')
        self.sysObjectID = data.get('SysObjectID')
        self.vendor = data.get('Vendor')
        self.vendorIcon = data.get('VendorIcon')
        self.machineType = data.get('MachineType')
        self.sysDescription = data.get('SysDescription')
        self.sysName = data.get('SysName')
        self.location = data.get('Location')
        self.contact = data.get('Contact')
        self.ignoredNodeID = data.get('IgnoredNodeID')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.iD = data.get('ID')
        self.profileID = data.get('ProfileID')
        self.netObjectID = data.get('NetObjectID')
        self.netObjectType = data.get('NetObjectType')
        self.pollerType = data.get('PollerType')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.profileID = data.get('ProfileID')
        self.discoveredNodeID = data.get('DiscoveredNodeID')
        self.volumeIndex = data.get('VolumeIndex')
        self.volumeType = data.get('VolumeType')
        self.volumeDescription = data.get('VolumeDescription')
        self.ignoredVolumeID = data.get('IgnoredVolumeID')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.profileID = data.get('ProfileID')
        self.name = data.get('Name')
        self.description = data.get('Description')
        self.runTimeInSeconds = data.get('RunTimeInSeconds')
        self.lastRun = data.get('LastRun')
        self.engineID = data.get('EngineID')
        self.status = data.get('Status')
        self.jobID = data.get('JobID')
        self.sIPPort = data.get('SIPPort')
        self.hopCount = data.get('HopCount')
        self.searchTimeout = data.get('SearchTimeout')
        self.sNMPTimeout = data.get('SNMPTimeout')
        self.sNMPRetries = data.get('SNMPRetries')
        self.repeatInterval = data.get('RepeatInterval')
        self.active = data.get('Active')
        self.duplicateNodes = data.get('DuplicateNodes')
        self.importUpInterface = data.get('ImportUpInterface')
        self.importDownInterface = data.get('ImportDownInterface')
        self.importShutdownInterface = data.get('ImportShutdownInterface')
        self.selectionMethod = data.get('SelectionMethod')
        self.jobTimeout = data.get('JobTimeout')
        self.scheduleRunAtTime = data.get('ScheduleRunAtTime')
        self.scheduleRunFrequency = data.get('ScheduleRunFrequency')
        self.statusDescription = data.get('StatusDescription')
        self.isHidden = data.get('IsHidden')
        self.isAutoImport = data.get('IsAutoImport')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.elementType = data.get('ElementType')
        self.maxElementCount = data.get('MaxElementCount')

    def getElementType(self):
        return self.elementType

    def getMaxElementCount(self):
        return self.maxElementCount


class OrionEvents():

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.eventID = data.get('EventID')
        self.eventTime = data.get('EventTime')
        self.networkNode = data.get('NetworkNode')
        self.netObjectID = data.get('NetObjectID')
        self.eventType = data.get('EventType')
        self.message = data.get('Message')
        self.acknowledged = data.get('Acknowledged')
        self.netObjectType = data.get('NetObjectType')
        self.timeStamp = data.get('TimeStamp')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.eventType = data.get('EventType')
        self.name = data.get('Name')
        self.bold = data.get('Bold')
        self.backColor = data.get('BackColor')
        self.icon = data.get('Icon')
        self.sort = data.get('Sort')
        self.notify = data.get('Notify')
        self.record = data.get('Record')
        self.sound = data.get('Sound')
        self.mute = data.get('Mute')
        self.notifyMessage = data.get('NotifyMessage')
        self.notifySubject = data.get('NotifySubject')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.nodeID = data.get('NodeID')
        self.iPAddress = data.get('IPAddress')
        self.iPAddressN = data.get('IPAddressN')
        self.iPAddressType = data.get('IPAddressType')
        self.interfaceIndex = data.get('InterfaceIndex')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.nodeID = data.get('NodeID')
        self.portID = data.get('PortID')
        self.mACAddress = data.get('MACAddress')
        self.status = data.get('Status')
        self.vlanId = data.get('VlanId')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.nodeID = data.get('NodeID')
        self.ifIndex = data.get('IfIndex')
        self.mACAddress = data.get('MACAddress')
        self.iPAddress = data.get('IPAddress')
        self.type = data.get('Type')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.nodeID = data.get('NodeID')
        self.localPortNumber = data.get('LocalPortNumber')
        self.remoteIfIndex = data.get('RemoteIfIndex')
        self.remotePortId = data.get('RemotePortId')
        self.remotePortDescription = data.get('RemotePortDescription')
        self.remoteSystemName = data.get('RemoteSystemName')
        self.remoteIpAddress = data.get('RemoteIpAddress')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.nodeID = data.get('NodeID')
        self.mAC = data.get('MAC')
        self.dateTime = data.get('DateTime')

    def getNodeID(self):
        return self.nodeID

    def getMAC(self):
        return self.mAC

    def getDateTime(self):
        return self.dateTime


class OrionNodes():

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.nodeID = data.get('NodeID')
        self.objectSubType = data.get('ObjectSubType')
        self.iPAddress = data.get('IPAddress')
        self.iPAddressType = data.get('IPAddressType')
        self.dynamicIP = data.get('DynamicIP')
        self.caption = data.get('Caption')
        self.nodeDescription = data.get('NodeDescription')
        self.dNS = data.get('DNS')
        self.sysName = data.get('SysName')
        self.vendor = data.get('Vendor')
        self.sysObjectID = data.get('SysObjectID')
        self.location = data.get('Location')
        self.contact = data.get('Contact')
        self.vendorIcon = data.get('VendorIcon')
        self.icon = data.get('Icon')
        self.iOSImage = data.get('IOSImage')
        self.iOSVersion = data.get('IOSVersion')
        self.groupStatus = data.get('GroupStatus')
        self.statusIcon = data.get('StatusIcon')
        self.lastBoot = data.get('LastBoot')
        self.systemUpTime = data.get('SystemUpTime')
        self.responseTime = data.get('ResponseTime')
        self.percentLoss = data.get('PercentLoss')
        self.avgResponseTime = data.get('AvgResponseTime')
        self.minResponseTime = data.get('MinResponseTime')
        self.maxResponseTime = data.get('MaxResponseTime')
        self.cPULoad = data.get('CPULoad')
        self.memoryUsed = data.get('MemoryUsed')
        self.percentMemoryUsed = data.get('PercentMemoryUsed')
        self.lastSync = data.get('LastSync')
        self.lastSystemUpTimePollUtc = data.get('LastSystemUpTimePollUtc')
        self.machineType = data.get('MachineType')
        self.severity = data.get('Severity')
        self.childStatus = data.get('ChildStatus')
        self.allow64BitCounters = data.get('Allow64BitCounters')
        self.agentPort = data.get('AgentPort')
        self.totalMemory = data.get('TotalMemory')
        self.cMTS = data.get('CMTS')
        self.customPollerLastStatisticsPoll = data.get(
            'CustomPollerLastStatisticsPoll')
        self.customPollerLastStatisticsPollSuccess = data.get(
            'CustomPollerLastStatisticsPollSuccess')
        self.sNMPVersion = data.get('SNMPVersion')
        self.pollInterval = data.get('PollInterval')
        self.engineID = data.get('EngineID')
        self.rediscoveryInterval = data.get('RediscoveryInterval')
        self.nextPoll = data.get('NextPoll')
        self.nextRediscovery = data.get('NextRediscovery')
        self.statCollection = data.get('StatCollection')
        self.external = data.get('External')
        self.community = data.get('Community')
        self.rWCommunity = data.get('RWCommunity')
        self.iP = data.get('IP')
        self.iP_Address = data.get('IP_Address')
        self.iPAddressGUID = data.get('IPAddressGUID')
        self.nodeName = data.get('NodeName')
        self.blockUntil = data.get('BlockUntil')
        self.bufferNoMemThisHour = data.get('BufferNoMemThisHour')
        self.bufferNoMemToday = data.get('BufferNoMemToday')
        self.bufferSmMissThisHour = data.get('BufferSmMissThisHour')
        self.bufferSmMissToday = data.get('BufferSmMissToday')
        self.bufferMdMissThisHour = data.get('BufferMdMissThisHour')
        self.bufferMdMissToday = data.get('BufferMdMissToday')
        self.bufferBgMissThisHour = data.get('BufferBgMissThisHour')
        self.bufferBgMissToday = data.get('BufferBgMissToday')
        self.bufferLgMissThisHour = data.get('BufferLgMissThisHour')
        self.bufferLgMissToday = data.get('BufferLgMissToday')
        self.bufferHgMissThisHour = data.get('BufferHgMissThisHour')
        self.bufferHgMissToday = data.get('BufferHgMissToday')
        self.orionIdPrefix = data.get('OrionIdPrefix')
        self.orionIdColumn = data.get('OrionIdColumn')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.nodeID = data.get('NodeID')
        self.city = data.get('City')
        self.comments = data.get('Comments')
        self.department = data.get('Department')

    def getNodeID(self):
        return self.nodeID

    def getCity(self):
        return self.city

    def getComments(self):
        return self.comments

    def getDepartment(self):
        return self.department


class OrionNodesStats():

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.avgResponseTime = data.get('AvgResponseTime')
        self.minResponseTime = data.get('MinResponseTime')
        self.maxResponseTime = data.get('MaxResponseTime')
        self.responseTime = data.get('ResponseTime')
        self.percentLoss = data.get('PercentLoss')
        self.cPULoad = data.get('CPULoad')
        self.memoryUsed = data.get('MemoryUsed')
        self.percentMemoryUsed = data.get('PercentMemoryUsed')
        self.lastBoot = data.get('LastBoot')
        self.systemUpTime = data.get('SystemUpTime')
        self.nodeID = data.get('NodeID')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.nodeID = data.get('NodeID')
        self.vlanId = data.get('VlanId')

    def getNodeID(self):
        return self.nodeID

    def getVlanId(self):
        return self.vlanId


class OrionNPMDiscoveredInterfaces():

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.profileID = data.get('ProfileID')
        self.discoveredNodeID = data.get('DiscoveredNodeID')
        self.discoveredInterfaceID = data.get('DiscoveredInterfaceID')
        self.interfaceIndex = data.get('InterfaceIndex')
        self.interfaceName = data.get('InterfaceName')
        self.interfaceType = data.get('InterfaceType')
        self.interfaceSubType = data.get('InterfaceSubType')
        self.interfaceTypeDescription = data.get('InterfaceTypeDescription')
        self.operStatus = data.get('OperStatus')
        self.adminStatus = data.get('AdminStatus')
        self.physicalAddress = data.get('PhysicalAddress')
        self.ifName = data.get('IfName')
        self.interfaceAlias = data.get('InterfaceAlias')
        self.interfaceTypeName = data.get('InterfaceTypeName')
        self.ignoredInterfaceID = data.get('IgnoredInterfaceID')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.dateTime = data.get('DateTime')
        self.interfaceID = data.get('InterfaceID')
        self.nodeID = data.get('NodeID')
        self.availability = data.get('Availability')
        self.weight = data.get('Weight')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.nodeID = data.get('NodeID')
        self.interfaceID = data.get('InterfaceID')
        self.dateTime = data.get('DateTime')
        self.archive = data.get('Archive')
        self.inErrors = data.get('InErrors')
        self.inDiscards = data.get('InDiscards')
        self.outErrors = data.get('OutErrors')
        self.outDiscards = data.get('OutDiscards')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.nodeID = data.get('NodeID')
        self.interfaceID = data.get('InterfaceID')
        self.objectSubType = data.get('ObjectSubType')
        self.name = data.get('Name')
        self.index = data.get('Index')
        self.icon = data.get('Icon')
        self.type = data.get('Type')
        self.typeName = data.get('TypeName')
        self.typeDescription = data.get('TypeDescription')
        self.speed = data.get('Speed')
        self.mTU = data.get('MTU')
        self.lastChange = data.get('LastChange')
        self.physicalAddress = data.get('PhysicalAddress')
        self.adminStatus = data.get('AdminStatus')
        self.operStatus = data.get('OperStatus')
        self.statusIcon = data.get('StatusIcon')
        self.inBandwidth = data.get('InBandwidth')
        self.outBandwidth = data.get('OutBandwidth')
        self.caption = data.get('Caption')
        self.fullName = data.get('FullName')
        self.outbps = data.get('Outbps')
        self.inbps = data.get('Inbps')
        self.outPercentUtil = data.get('OutPercentUtil')
        self.inPercentUtil = data.get('InPercentUtil')
        self.outPps = data.get('OutPps')
        self.inPps = data.get('InPps')
        self.inPktSize = data.get('InPktSize')
        self.outPktSize = data.get('OutPktSize')
        self.outUcastPps = data.get('OutUcastPps')
        self.outMcastPps = data.get('OutMcastPps')
        self.inUcastPps = data.get('InUcastPps')
        self.inMcastPps = data.get('InMcastPps')
        self.inDiscardsThisHour = data.get('InDiscardsThisHour')
        self.inDiscardsToday = data.get('InDiscardsToday')
        self.inErrorsThisHour = data.get('InErrorsThisHour')
        self.inErrorsToday = data.get('InErrorsToday')
        self.outDiscardsThisHour = data.get('OutDiscardsThisHour')
        self.outDiscardsToday = data.get('OutDiscardsToday')
        self.outErrorsThisHour = data.get('OutErrorsThisHour')
        self.outErrorsToday = data.get('OutErrorsToday')
        self.maxInBpsToday = data.get('MaxInBpsToday')
        self.maxInBpsTime = data.get('MaxInBpsTime')
        self.maxOutBpsToday = data.get('MaxOutBpsToday')
        self.maxOutBpsTime = data.get('MaxOutBpsTime')
        self.counter64 = data.get('Counter64')
        self.lastSync = data.get('LastSync')
        self.alias = data.get('Alias')
        self.ifName = data.get('IfName')
        self.severity = data.get('Severity')
        self.customBandwidth = data.get('CustomBandwidth')
        self.customPollerLastStatisticsPoll = data.get(
            'CustomPollerLastStatisticsPoll')
        self.pollInterval = data.get('PollInterval')
        self.nextPoll = data.get('NextPoll')
        self.rediscoveryInterval = data.get('RediscoveryInterval')
        self.nextRediscovery = data.get('NextRediscovery')
        self.statCollection = data.get('StatCollection')
        self.unPluggable = data.get('UnPluggable')
        self.interfaceSpeed = data.get('InterfaceSpeed')
        self.interfaceCaption = data.get('InterfaceCaption')
        self.interfaceType = data.get('InterfaceType')
        self.interfaceSubType = data.get('InterfaceSubType')
        self.mAC = data.get('MAC')
        self.interfaceName = data.get('InterfaceName')
        self.interfaceIcon = data.get('InterfaceIcon')
        self.interfaceTypeName = data.get('InterfaceTypeName')
        self.adminStatusLED = data.get('AdminStatusLED')
        self.operStatusLED = data.get('OperStatusLED')
        self.interfaceAlias = data.get('InterfaceAlias')
        self.interfaceIndex = data.get('InterfaceIndex')
        self.interfaceLastChange = data.get('InterfaceLastChange')
        self.interfaceMTU = data.get('InterfaceMTU')
        self.interfaceTypeDescription = data.get('InterfaceTypeDescription')
        self.orionIdPrefix = data.get('OrionIdPrefix')
        self.orionIdColumn = data.get('OrionIdColumn')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.nodeID = data.get('NodeID')
        self.interfaceID = data.get('InterfaceID')
        self.dateTime = data.get('DateTime')
        self.archive = data.get('Archive')
        self.inAveragebps = data.get('InAveragebps')
        self.inMinbps = data.get('InMinbps')
        self.inMaxbps = data.get('InMaxbps')
        self.inTotalBytes = data.get('InTotalBytes')
        self.inTotalPkts = data.get('InTotalPkts')
        self.inAvgUniCastPkts = data.get('InAvgUniCastPkts')
        self.inMinUniCastPkts = data.get('InMinUniCastPkts')
        self.inMaxUniCastPkts = data.get('InMaxUniCastPkts')
        self.inAvgMultiCastPkts = data.get('InAvgMultiCastPkts')
        self.inMinMultiCastPkts = data.get('InMinMultiCastPkts')
        self.inMaxMultiCastPkts = data.get('InMaxMultiCastPkts')
        self.outAveragebps = data.get('OutAveragebps')
        self.outMinbps = data.get('OutMinbps')
        self.outMaxbps = data.get('OutMaxbps')
        self.outTotalBytes = data.get('OutTotalBytes')
        self.outTotalPkts = data.get('OutTotalPkts')
        self.outAvgUniCastPkts = data.get('OutAvgUniCastPkts')
        self.outMaxUniCastPkts = data.get('OutMaxUniCastPkts')
        self.outMinUniCastPkts = data.get('OutMinUniCastPkts')
        self.outAvgMultiCastPkts = data.get('OutAvgMultiCastPkts')
        self.outMinMultiCastPkts = data.get('OutMinMultiCastPkts')
        self.outMaxMultiCastPkts = data.get('OutMaxMultiCastPkts')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.pollerID = data.get('PollerID')
        self.pollerType = data.get('PollerType')
        self.netObject = data.get('NetObject')
        self.netObjectType = data.get('NetObjectType')
        self.netObjectID = data.get('NetObjectID')
        self.enabled = data.get('Enabled')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.reportID = data.get('ReportID')
        self.name = data.get('Name')
        self.category = data.get('Category')
        self.title = data.get('Title')
        self.type = data.get('Type')
        self.subTitle = data.get('SubTitle')
        self.description = data.get('Description')
        self.legacyPath = data.get('LegacyPath')
        self.definition = data.get('Definition')
        self.moduleTitle = data.get('ModuleTitle')
        self.recipientList = data.get('RecipientList')
        self.limitationCategory = data.get('LimitationCategory')
        self.owner = data.get('Owner')
        self.lastRenderDuration = data.get('LastRenderDuration')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.nodeID = data.get('NodeID')
        self.dateTime = data.get('DateTime')
        self.archive = data.get('Archive')
        self.avgResponseTime = data.get('AvgResponseTime')
        self.minResponseTime = data.get('MinResponseTime')
        self.maxResponseTime = data.get('MaxResponseTime')
        self.percentLoss = data.get('PercentLoss')
        self.availability = data.get('Availability')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.displayName = data.get('DisplayName')
        self.serviceName = data.get('ServiceName')
        self.status = data.get('Status')
        self.memory = data.get('Memory')

    def getDisplayName(self):
        return self.displayName

    def getServiceName(self):
        return self.serviceName

    def getStatus(self):
        return self.status

    def getMemory(self):
        return self.memory


class OrionSysLog():

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.messageID = data.get('MessageID')
        self.engineID = data.get('EngineID')
        self.dateTime = data.get('DateTime')
        self.iPAddress = data.get('IPAddress')
        self.acknowledged = data.get('Acknowledged')
        self.sysLogFacility = data.get('SysLogFacility')
        self.sysLogSeverity = data.get('SysLogSeverity')
        self.hostname = data.get('Hostname')
        self.messageType = data.get('MessageType')
        self.message = data.get('Message')
        self.sysLogTag = data.get('SysLogTag')
        self.firstIPInMessage = data.get('FirstIPInMessage')
        self.secIPInMessage = data.get('SecIPInMessage')
        self.macInMessage = data.get('MacInMessage')
        self.timeStamp = data.get('TimeStamp')
        self.nodeID = data.get('NodeID')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.discoveryProfileID = data.get('DiscoveryProfileID')
        self.srcNodeID = data.get('SrcNodeID')
        self.srcInterfaceID = data.get('SrcInterfaceID')
        self.destNodeID = data.get('DestNodeID')
        self.destInterfaceID = data.get('DestInterfaceID')
        self.srcType = data.get('SrcType')
        self.destType = data.get('DestType')
        self.dataSourceNodeID = data.get('DataSourceNodeID')
        self.lastUpdateUtc = data.get('LastUpdateUtc')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.trapID = data.get('TrapID')
        self.engineID = data.get('EngineID')
        self.dateTime = data.get('DateTime')
        self.iPAddress = data.get('IPAddress')
        self.community = data.get('Community')
        self.tag = data.get('Tag')
        self.acknowledged = data.get('Acknowledged')
        self.hostname = data.get('Hostname')
        self.nodeID = data.get('NodeID')
        self.trapType = data.get('TrapType')
        self.colorCode = data.get('ColorCode')
        self.timeStamp = data.get('TimeStamp')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.viewID = data.get('ViewID')
        self.viewKey = data.get('ViewKey')
        self.viewTitle = data.get('ViewTitle')
        self.viewType = data.get('ViewType')
        self.columns = data.get('Columns')
        self.column1Width = data.get('Column1Width')
        self.column2Width = data.get('Column2Width')
        self.column3Width = data.get('Column3Width')
        self.system = data.get('System')
        self.customizable = data.get('Customizable')
        self.limitationID = data.get('LimitationID')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.clusterID = data.get('ClusterID')
        self.managedObjectID = data.get('ManagedObjectID')
        self.dataCenterID = data.get('DataCenterID')
        self.name = data.get('Name')
        self.totalMemory = data.get('TotalMemory')
        self.totalCpu = data.get('TotalCpu')
        self.cpuCoreCount = data.get('CpuCoreCount')
        self.cpuThreadCount = data.get('CpuThreadCount')
        self.effectiveCpu = data.get('EffectiveCpu')
        self.effectiveMemory = data.get('EffectiveMemory')
        self.drsBehaviour = data.get('DrsBehaviour')
        self.drsStatus = data.get('DrsStatus')
        self.drsVmotionRate = data.get('DrsVmotionRate')
        self.haAdmissionControlStatus = data.get('HaAdmissionControlStatus')
        self.haStatus = data.get('HaStatus')
        self.haFailoverLevel = data.get('HaFailoverLevel')
        self.configStatus = data.get('ConfigStatus')
        self.overallStatus = data.get('OverallStatus')
        self.cPULoad = data.get('CPULoad')
        self.cPUUsageMHz = data.get('CPUUsageMHz')
        self.memoryUsage = data.get('MemoryUsage')
        self.memoryUsageMB = data.get('MemoryUsageMB')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.clusterID = data.get('ClusterID')
        self.dateTime = data.get('DateTime')
        self.percentAvailability = data.get('PercentAvailability')
        self.minCPULoad = data.get('MinCPULoad')
        self.maxCPULoad = data.get('MaxCPULoad')
        self.avgCPULoad = data.get('AvgCPULoad')
        self.minCPUUsageMHz = data.get('MinCPUUsageMHz')
        self.maxCPUUsageMHz = data.get('MaxCPUUsageMHz')
        self.avgCPUUsageMHz = data.get('AvgCPUUsageMHz')
        self.minMemoryUsage = data.get('MinMemoryUsage')
        self.maxMemoryUsage = data.get('MaxMemoryUsage')
        self.avgMemoryUsage = data.get('AvgMemoryUsage')
        self.minMemoryUsageMB = data.get('MinMemoryUsageMB')
        self.maxMemoryUsageMB = data.get('MaxMemoryUsageMB')
        self.avgMemoryUsageMB = data.get('AvgMemoryUsageMB')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.dataCenterID = data.get('DataCenterID')
        self.managedObjectID = data.get('ManagedObjectID')
        self.vCenterID = data.get('VCenterID')
        self.name = data.get('Name')
        self.configStatus = data.get('ConfigStatus')
        self.overallStatus = data.get('OverallStatus')
        self.managedStatus = data.get('ManagedStatus')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.hostID = data.get('HostID')
        self.iPAddress = data.get('IPAddress')

    def getHostID(self):
        return self.hostID

    def getIPAddress(self):
        return self.iPAddress


class OrionVIMHosts():

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.hostID = data.get('HostID')
        self.managedObjectID = data.get('ManagedObjectID')
        self.nodeID = data.get('NodeID')
        self.hostName = data.get('HostName')
        self.clusterID = data.get('ClusterID')
        self.dataCenterID = data.get('DataCenterID')
        self.vMwareProductName = data.get('VMwareProductName')
        self.vMwareProductVersion = data.get('VMwareProductVersion')
        self.pollingJobID = data.get('PollingJobID')
        self.serviceURIID = data.get('ServiceURIID')
        self.credentialID = data.get('CredentialID')
        self.hostStatus = data.get('HostStatus')
        self.pollingMethod = data.get('PollingMethod')
        self.model = data.get('Model')
        self.vendor = data.get('Vendor')
        self.processorType = data.get('ProcessorType')
        self.cpuCoreCount = data.get('CpuCoreCount')
        self.cpuPkgCount = data.get('CpuPkgCount')
        self.cpuMhz = data.get('CpuMhz')
        self.nicCount = data.get('NicCount')
        self.hbaCount = data.get('HbaCount')
        self.hbaFcCount = data.get('HbaFcCount')
        self.hbaScsiCount = data.get('HbaScsiCount')
        self.hbaIscsiCount = data.get('HbaIscsiCount')
        self.memorySize = data.get('MemorySize')
        self.buildNumber = data.get('BuildNumber')
        self.biosSerial = data.get('BiosSerial')
        self.iPAddress = data.get('IPAddress')
        self.connectionState = data.get('ConnectionState')
        self.configStatus = data.get('ConfigStatus')
        self.overallStatus = data.get('OverallStatus')
        self.nodeStatus = data.get('NodeStatus')
        self.networkUtilization = data.get('NetworkUtilization')
        self.networkUsageRate = data.get('NetworkUsageRate')
        self.networkTransmitRate = data.get('NetworkTransmitRate')
        self.networkReceiveRate = data.get('NetworkReceiveRate')
        self.networkCapacityKbps = data.get('NetworkCapacityKbps')
        self.cpuLoad = data.get('CpuLoad')
        self.cpuUsageMHz = data.get('CpuUsageMHz')
        self.memUsage = data.get('MemUsage')
        self.memUsageMB = data.get('MemUsageMB')
        self.vmCount = data.get('VmCount')
        self.vmRunningCount = data.get('VmRunningCount')
        self.statusMessage = data.get('StatusMessage')
        self.platformID = data.get('PlatformID')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.hostID = data.get('HostID')
        self.dateTime = data.get('DateTime')
        self.vmCount = data.get('VmCount')
        self.vmRunningCount = data.get('VmRunningCount')
        self.minNetworkUtilization = data.get('MinNetworkUtilization')
        self.maxNetworkUtilization = data.get('MaxNetworkUtilization')
        self.avgNetworkUtilization = data.get('AvgNetworkUtilization')
        self.minNetworkUsageRate = data.get('MinNetworkUsageRate')
        self.maxNetworkUsageRate = data.get('MaxNetworkUsageRate')
        self.avgNetworkUsageRate = data.get('AvgNetworkUsageRate')
        self.minNetworkTransmitRate = data.get('MinNetworkTransmitRate')
        self.maxNetworkTransmitRate = data.get('MaxNetworkTransmitRate')
        self.avgNetworkTransmitRate = data.get('AvgNetworkTransmitRate')
        self.minNetworkReceiveRate = data.get('MinNetworkReceiveRate')
        self.maxNetworkReceiveRate = data.get('MaxNetworkReceiveRate')
        self.avgNetworkReceiveRate = data.get('AvgNetworkReceiveRate')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.status = data.get('Status')
        self.statusDescription = data.get('StatusDescription')
        self.statusLED = data.get('StatusLED')
        self.unManaged = data.get('UnManaged')
        self.unManageFrom = data.get('UnManageFrom')
        self.unManageUntil = data.get('UnManageUntil')
        self.triggeredAlarmDescription = data.get('TriggeredAlarmDescription')
        self.detailsUrl = data.get('DetailsUrl')
        self.image = data.get('Image')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.resourcePoolID = data.get('ResourcePoolID')
        self.managedObjectID = data.get('ManagedObjectID')
        self.name = data.get('Name')
        self.cpuMaxUsage = data.get('CpuMaxUsage')
        self.cpuOverallUsage = data.get('CpuOverallUsage')
        self.cpuReservationUsedForVM = data.get('CpuReservationUsedForVM')
        self.cpuReservationUsed = data.get('CpuReservationUsed')
        self.memMaxUsage = data.get('MemMaxUsage')
        self.memOverallUsage = data.get('MemOverallUsage')
        self.memReservationUsedForVM = data.get('MemReservationUsedForVM')
        self.memReservationUsed = data.get('MemReservationUsed')
        self.lastModifiedTime = data.get('LastModifiedTime')
        self.cpuExpandable = data.get('CpuExpandable')
        self.cpuLimit = data.get('CpuLimit')
        self.cpuReservation = data.get('CpuReservation')
        self.cpuShareLevel = data.get('CpuShareLevel')
        self.cpuShareCount = data.get('CpuShareCount')
        self.memExpandable = data.get('MemExpandable')
        self.memLimit = data.get('MemLimit')
        self.memReservation = data.get('MemReservation')
        self.memShareLevel = data.get('MemShareLevel')
        self.memShareCount = data.get('MemShareCount')
        self.configStatus = data.get('ConfigStatus')
        self.overallStatus = data.get('OverallStatus')
        self.managedStatus = data.get('ManagedStatus')
        self.clusterID = data.get('ClusterID')
        self.vCenterID = data.get('VCenterID')
        self.parentResourcePoolID = data.get('ParentResourcePoolID')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.thresholdID = data.get('ThresholdID')
        self.typeID = data.get('TypeID')
        self.warning = data.get('Warning')
        self.high = data.get('High')
        self.maximum = data.get('Maximum')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.typeID = data.get('TypeID')
        self.name = data.get('Name')
        self.information = data.get('Information')
        self.warning = data.get('Warning')
        self.high = data.get('High')
        self.maximum = data.get('Maximum')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.vCenterID = data.get('VCenterID')
        self.nodeID = data.get('NodeID')
        self.name = data.get('Name')
        self.vMwareProductName = data.get('VMwareProductName')
        self.vMwareProductVersion = data.get('VMwareProductVersion')
        self.pollingJobID = data.get('PollingJobID')
        self.serviceURIID = data.get('ServiceURIID')
        self.credentialID = data.get('CredentialID')
        self.hostStatus = data.get('HostStatus')
        self.model = data.get('Model')
        self.vendor = data.get('Vendor')
        self.buildNumber = data.get('BuildNumber')
        self.biosSerial = data.get('BiosSerial')
        self.iPAddress = data.get('IPAddress')
        self.connectionState = data.get('ConnectionState')
        self.statusMessage = data.get('StatusMessage')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.virtualMachineID = data.get('VirtualMachineID')
        self.managedObjectID = data.get('ManagedObjectID')
        self.uUID = data.get('UUID')
        self.hostID = data.get('HostID')
        self.nodeID = data.get('NodeID')
        self.resourcePoolID = data.get('ResourcePoolID')
        self.vMConfigFile = data.get('VMConfigFile')
        self.memoryConfigured = data.get('MemoryConfigured')
        self.memoryShares = data.get('MemoryShares')
        self.cPUShares = data.get('CPUShares')
        self.guestState = data.get('GuestState')
        self.iPAddress = data.get('IPAddress')
        self.logDirectory = data.get('LogDirectory')
        self.guestVmWareToolsVersion = data.get('GuestVmWareToolsVersion')
        self.guestVmWareToolsStatus = data.get('GuestVmWareToolsStatus')
        self.name = data.get('Name')
        self.guestName = data.get('GuestName')
        self.guestFamily = data.get('GuestFamily')
        self.guestDnsName = data.get('GuestDnsName')
        self.nicCount = data.get('NicCount')
        self.vDisksCount = data.get('VDisksCount')
        self.processorCount = data.get('ProcessorCount')
        self.powerState = data.get('PowerState')
        self.bootTime = data.get('BootTime')
        self.configStatus = data.get('ConfigStatus')
        self.overallStatus = data.get('OverallStatus')
        self.nodeStatus = data.get('NodeStatus')
        self.networkUsageRate = data.get('NetworkUsageRate')
        self.networkTransmitRate = data.get('NetworkTransmitRate')
        self.networkReceiveRate = data.get('NetworkReceiveRate')
        self.cpuLoad = data.get('CpuLoad')
        self.cpuUsageMHz = data.get('CpuUsageMHz')
        self.memUsage = data.get('MemUsage')
        self.memUsageMB = data.get('MemUsageMB')
        self.isLicensed = data.get('IsLicensed')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.virtualMachineID = data.get('VirtualMachineID')
        self.dateTime = data.get('DateTime')
        self.minCPULoad = data.get('MinCPULoad')
        self.maxCPULoad = data.get('MaxCPULoad')
        self.avgCPULoad = data.get('AvgCPULoad')
        self.minMemoryUsage = data.get('MinMemoryUsage')
        self.maxMemoryUsage = data.get('MaxMemoryUsage')
        self.avgMemoryUsage = data.get('AvgMemoryUsage')
        self.minNetworkUsageRate = data.get('MinNetworkUsageRate')
        self.maxNetworkUsageRate = data.get('MaxNetworkUsageRate')
        self.avgNetworkUsageRate = data.get('AvgNetworkUsageRate')
        self.minNetworkTransmitRate = data.get('MinNetworkTransmitRate')
        self.maxNetworkTransmitRate = data.get('MaxNetworkTransmitRate')
        self.avgNetworkTransmitRate = data.get('AvgNetworkTransmitRate')
        self.minNetworkReceiveRate = data.get('MinNetworkReceiveRate')
        self.maxNetworkReceiveRate = data.get('MaxNetworkReceiveRate')
        self.avgNetworkReceiveRate = data.get('AvgNetworkReceiveRate')
        self.availability = data.get('Availability')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.nodeID = data.get('NodeID')
        self.volumeID = data.get('VolumeID')
        self.dateTime = data.get('DateTime')
        self.avgDiskQueueLength = data.get('AvgDiskQueueLength')
        self.minDiskQueueLength = data.get('MinDiskQueueLength')
        self.maxDiskQueueLength = data.get('MaxDiskQueueLength')
        self.avgDiskTransfer = data.get('AvgDiskTransfer')
        self.minDiskTransfer = data.get('MinDiskTransfer')
        self.maxDiskTransfer = data.get('MaxDiskTransfer')
        self.avgDiskReads = data.get('AvgDiskReads')
        self.minDiskReads = data.get('MinDiskReads')
        self.maxDiskReads = data.get('MaxDiskReads')
        self.avgDiskWrites = data.get('AvgDiskWrites')
        self.minDiskWrites = data.get('MinDiskWrites')
        self.maxDiskWrites = data.get('MaxDiskWrites')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.nodeID = data.get('NodeID')
        self.volumeID = data.get('VolumeID')
        self.icon = data.get('Icon')
        self.index = data.get('Index')
        self.caption = data.get('Caption')
        self.pollInterval = data.get('PollInterval')
        self.statCollection = data.get('StatCollection')
        self.rediscoveryInterval = data.get('RediscoveryInterval')
        self.statusIcon = data.get('StatusIcon')
        self.type = data.get('Type')
        self.size = data.get('Size')
        self.responding = data.get('Responding')
        self.fullName = data.get('FullName')
        self.lastSync = data.get('LastSync')
        self.volumePercentUsed = data.get('VolumePercentUsed')
        self.volumeAllocationFailuresThisHour = data.get(
            'VolumeAllocationFailuresThisHour')
        self.volumeIndex = data.get('VolumeIndex')
        self.volumeType = data.get('VolumeType')
        self.volumeDescription = data.get('VolumeDescription')
        self.volumeSize = data.get('VolumeSize')
        self.volumeSpaceUsed = data.get('VolumeSpaceUsed')
        self.volumeAllocationFailuresToday = data.get(
            'VolumeAllocationFailuresToday')
        self.volumeResponding = data.get('VolumeResponding')
        self.volumeSpaceAvailable = data.get('VolumeSpaceAvailable')
        self.volumeTypeIcon = data.get('VolumeTypeIcon')
        self.orionIdPrefix = data.get('OrionIdPrefix')
        self.orionIdColumn = data.get('OrionIdColumn')
        self.diskQueueLength = data.get('DiskQueueLength')
        self.diskTransfer = data.get('DiskTransfer')
        self.diskReads = data.get('DiskReads')
        self.diskWrites = data.get('DiskWrites')
        self.totalDiskIOPS = data.get('TotalDiskIOPS')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.percentUsed = data.get('PercentUsed')
        self.spaceUsed = data.get('SpaceUsed')
        self.spaceAvailable = data.get('SpaceAvailable')
        self.allocationFailuresThisHour = data.get(
            'AllocationFailuresThisHour')
        self.allocationFailuresToday = data.get('AllocationFailuresToday')
        self.diskQueueLength = data.get('DiskQueueLength')
        self.diskTransfer = data.get('DiskTransfer')
        self.diskReads = data.get('DiskReads')
        self.diskWrites = data.get('DiskWrites')
        self.totalDiskIOPS = data.get('TotalDiskIOPS')
        self.volumeID = data.get('VolumeID')

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

    def __init__(self, **kwargs):
        requiredArgs = []
        optionalArgs = ['data', 'connection']
        ar = argChecker(requiredArgs, optionalArgs, kwargs.iteritems())
        data = ar['data']
        self.data = ar['data']
        self.connection = ar['connection']
        self.nodeID = data.get('NodeID')
        self.volumeID = data.get('VolumeID')
        self.dateTime = data.get('DateTime')
        self.diskSize = data.get('DiskSize')
        self.avgDiskUsed = data.get('AvgDiskUsed')
        self.minDiskUsed = data.get('MinDiskUsed')
        self.maxDiskUsed = data.get('MaxDiskUsed')
        self.percentDiskUsed = data.get('PercentDiskUsed')
        self.allocationFailures = data.get('AllocationFailures')

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
