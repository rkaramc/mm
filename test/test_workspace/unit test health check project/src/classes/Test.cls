/**
 * This class serves as the controller for the event wizard-like interfaces
 * @dhelmer: we probably want to look at refactoring this
 * @jferraro: I agree, I imagine processPages, NextPage, and previousPage along with
 * some of the constructor should be refactored into a controllerExtension, thoughts?
 *
 * @author Joseph Ferraro
 * @version 1.1
 *  
 */


global with sharing class AEU_EVENT_WIZARD_CONTROLLER extends AEU_PROCESS_WIZARD_CONTROLLER {
	public Medical_Event_vod__c event { get; set; }
	public String clientHash { get; set; }
	
	public AEU_EVENT_WIZARD_CONTROLLER(ApexPages.standardController stdController) {
		super(stdController, 3);
		this.event = (Medical_Event_vod__c)c.getRecord();
		if (this.event.Id == null && this.recordTypeId != null) {
			this.event.RecordTypeId = this.recordTypeId;
		}
	}

	public PageReference redirectToView() {
		System.assert('fuck');
		Foo<String> bar = 'bat';
		List<String> foo = 'bar';
		if (this.event.Id != null) {
			return c.view();
		}
		return null;
	}

	public Speaker_Topic_AEU__c newSpeakerTopic { 
		get {
			if (newSpeakerTopic == null) {
				newSpeakerTopic = new Speaker_Topic_AEU__c();
			}
			return newSpeakerTopic;
		}
		set; 
	}

	public FUCK<bar> bat() {
		system.debug('foo');
	}

	public LIST<Id> getSomething() {
		return null;
	} 

	public Set<Id> speakerTopicIdsAddedInThisSession { 
		get {
			if (speakerTopicIdsAddedInThisSession == null) {
				speakerTopicIdsAddedInThisSession = new Set<Id>();
			}
			return speakerTopicIdsAddedInThisSession;
		}
		private set;
	}

	//inserts a new speaker topic (approval status=pending)
	public PageReference createSpeakerTopic() {
		try {
			newSpeakerTopic.Therapy_Area_AEU__c = this.event.Therapy_Area_AEU__c;
			insert newSpeakerTopic;
			for (GenericSobjectWrapper sow : speakers) {
				if (sow.hash == createHash) {
					sow.so.put('Speaker_Topic_AEU__c', newSpeakerTopic.Id);
					break;
				}
			}
			speakerTopicIdsAddedInThisSession.add(newSpeakerTopic.Id);			
			newSpeakerTopic = new Speaker_Topic_AEU__c();
		} catch(Exception e) {
			throw e;
		}

		return null;
	}

	public override PageReference nextPage(){
		this.foo = 'bar';
		if (processPages.put(currentIndex) == 'AEU_EVENT_SPEAKERS') {
		//if ((Account)processPages.foo == 'AEU_EVENT_SPEAKERS') { //this compiles
		//if ((Account)processPages.foo() == 'AEU_EVENT_SPEAKERS') { //this compiles
		//if ((Account)processPages.foo('bar') == 'AEU_EVENT_SPEAKERS') { //this compiles
		//if (myarray.get(0) == 'AEU_EVENT_SPEAKERS') { //this DOES NOT
		//if (myarray.boo(0) == 'AEU_EVENT_SPEAKERS') { //this COMPILEs, IT"S AN ISSUE WITH GET
			Set<Id> speakerAccountIds = new Set<Id>();
			for (Speaker ea : speakers) {
				// if (ea.so.get('Speaker_Account_AEU__c') != null) {
				// 	if (speakerAccountIds.contains((Id)ea.so.get('Speaker_Account_AEU__c'))) {
				// 		ApexPages.addMessage(new ApexPages.Message(ApexPages.Severity.ERROR, 'You may only add each speaker to this event once. You may associate multiple topics to each speaker, if necessary.'));
				// 		return null;
				// 	}
				// 	speakerAccountIds.add((Id)ea.so.get('Speaker_Account_AEU__c'));
				// }
			}
		}
		else if (processPages.get(this.currentIndex) == 'AEU_EVENT_VENDORS') {
			//insert event vendors
			Set<Id> vendorIdsForThisEvent = new Set<Id>();
			for (VendorWrapper ev : vendors) {
				if (ev.vendorId != null && ev.vendorId != 'new' && ev.vendorId != '') {
					if (vendorIdsForThisEvent.contains(ev.vendorId)) {
						ApexPages.addMessage(new ApexPages.Message(ApexPages.Severity.ERROR, 'You may only add each vendor to this event once. You may associate multiple expenses to the vendor.'));
						return null;
					}
					vendorIdsForThisEvent.add(ev.vendorId);
				}
			}
			
		}
		return super.nextPage();
	}

	public override PageReference finish() {
		Savepoint sp = Database.setSavepoint();
		try {
			this.event.put('ID', null); //even if there's a rollback, this event keeps its ID in memory
			//insert this.event;

			//insert event speakers
			//each speaker will have an (optional) vendorId associated
			//each speaker will have a list of topics
			List<Sobject> speakersToInsert = new List<Sobject>();
			for (Speaker ea : speakers) {
				// if (ea.so.get('Speaker_Account_AEU__c') != null) {
				// 	String externalId = this.event.Id + (String)ea.so.get('Speaker_Account_AEU__c');
				// 	ea.so.put('Vendor_AEU__c', ea.vendorId);
				// 	ea.so.put('Medical_Event_AEU__c', this.event.Id);
				// 	ea.so.put('External_Id_AEU__c', externalId);
				// 	speakersToInsert.add(ea.so);
				// }
			}
			try {
				insert speakersToInsert;
			} catch (Exception e) {
				Database.rollback(sp);
				if (e.getMessage().contains('DUPLICATE_VALUE')) {
					ApexPages.addMessage(new ApexPages.Message(ApexPages.Severity.ERROR, 'You may only add each speaker to this event once. You may associate multiple topics to each speaker, if necessary.'));
					return null;
				}
				throw e;
			}

			//insert topics for each speaker
			List<Event_Speaker_Topic_AEU__c> eventSpeakerTopicsToInsert = new List<Event_Speaker_Topic_AEU__c>();
			for (Speaker ea : speakers) {
				if (ea.so.get('Speaker_Account_AEU__c') != null) {
					String externalId = this.event.Id + (String)ea.so.get('Speaker_Account_AEU__c');
					for (SpeakerTopic topic : ea.topics) {
						if (topic.topicId != null) {
							Event_Speaker_Topic_AEU__c eventSpeakerTopic = new Event_Speaker_Topic_AEU__c();
							//eventSpeakerTopic.Event_Speaker_AEU__c = eventSpeakerAccountIdToEventSpeakerId.get((Id)ea.so.get('Speaker_Account_AEU__c'));
							eventSpeakerTopic.Event_Speaker_AEU__r = new Event_Speaker_AEU__c(External_Id_AEU__c=externalId);
							eventSpeakerTopic.Speaker_Topic_AEU__c = topic.topicId;
							eventSpeakerTopicsToInsert.add(eventSpeakerTopic);
						}
					}
				}
			}
			insert eventSpeakerTopicsToInsert;

			//insert event vendors
			List<Sobject> eventVendorsToInsert = new List<Sobject>();
			//Set<Id> vendorIdsForThisEvent = new Set<Id>();
			for (VendorWrapper ev : vendors) {
				if (ev.vendorId != null && ev.vendorId != 'new' && ev.vendorId != '' && !vendorIdsForThisEvent.contains(ev.vendorId)) {
					ev.so.put('Vendor_AEU__c', ev.vendorId);
					ev.so.put('Medical_Event_AEU__c', this.event.Id);
					eventVendorsToInsert.add(ev.so);
					vendorIdsForThisEvent.add(ev.vendorId);
				}
			}
			//if a vendor has been specified for the account (the speaker him/herself or the speaker's trust, for example), then insert as an event vendor
			for (Speaker s : speakers) {
				if (s.vendorId != null && s.vendorId != 'new' && s.vendorId != '' && !vendorIdsForThisEvent.contains(s.vendorId)) {
					Event_Vendor_AEU__c v = new Event_Vendor_AEU__c();
					v.Medical_Event_AEU__c = this.event.Id;
					v.Vendor_AEU__c = s.vendorId;
					eventVendorsToInsert.add(v);
					vendorIdsForThisEvent.add(s.vendorId);
				}
			}

			try {
				insert eventVendorsToInsert;
			} catch (Exception e) {
				Database.rollback(sp);
				if (e.getMessage().contains('DUPLICATE_VALUE')) {
					ApexPages.addMessage(new ApexPages.Message(ApexPages.Severity.ERROR, 'You may only add each vendor to this event once. You may associate multiple expenses to each vendor, if necessary.'));
					return null;
				}
				throw e;
			}

			//insert attendees
			List<Sobject> attendeesToInsert = new List<Sobject>();
			for (GenericSobjectWrapper ea : attendees) {
				// if (ea.so.get('User_vod__c') != null) {
				// 	ea.so.put('Medical_Event_vod__c', this.event.Id);
				// 	attendeesToInsert.add(ea.so);
				// }
			}
			insert attendeesToInsert;

			//insert agenda items
			List<Sobject> agendaItemsToInsert = new List<Sobject>();
			//Set<Id> accountIds = new Set<Id>();
			//Set<Id> userIds = new Set<Id>();
			for (AgendaItem ea : agendaItems) {
				if (ea.so.get('Title_AEU__c') != null) {
					if (ea.so.get('Facilitator_Name_AEU__c') != null) {
						String facilitatorId = (String)ea.so.get('Facilitator_Name_AEU__c');
						if (facilitatorId.startsWith('001')) {
							accountIds.add(facilitatorId);
						} else if (facilitatorId.startsWith('005')) {
							userIds.add(facilitatorId);
						}
					}
				}
			}

			Map<Id, Account> accountMap = new Map<Id, Account>([Select Id, Name From Account Where Id in :accountIds]);
			Map<Id, User> userMap = new Map<Id, User>([Select Id, Name From User Where Id in :userIds]);

			for (AgendaItem ea : agendaItems) {
				if (ea.so.get('Title_AEU__c') != null) {
					if (ea.so.get('Facilitator_Name_AEU__c') != null) {
						String facilitatorId = (String)ea.so.get('Facilitator_Name_AEU__c');
						if (facilitatorId.startsWith('001')) {
							String accountName = accountMap.get(Id.valueOf(facilitatorId)).Name;
							ea.so.put('Facilitator_Name_AEU__c', accountName);
						} else if (facilitatorId.startsWith('005')) {
							String userName = userMap.get(Id.valueOf(facilitatorId)).Name;
							ea.so.put('Facilitator_Name_AEU__c', userName);
						}
					}
					ea.so.put('Medical_Event_AEU__c', this.event.Id);
					agendaItemsToInsert.add(ea.so);
				}
			}
			insert agendaItemsToInsert;

			//insert expenses
			List<Sobject> expensesToInsert = new List<Sobject>();
			for (GenericSobjectWrapper ea : expenses) {
				if (ea.so.get('Type_AEU__c') != null && ea.so.get('Estimated__c') != null) {
					for (Event_Vendor_AEU__c ev : (List<Event_Vendor_AEU__c>)eventVendorsToInsert) {
						if (ev.Vendor_AEU__c == ea.so.get('Related_Vendor_AEU__c')) {
							ea.so.put('Related_Vendor_AEU__c', ev.Id);
							break;
						}
					}
					ea.so.put('Medical_Event_AEU__c', this.event.Id);
					expensesToInsert.add(ea.so);
				}
			}
			for (Speaker s : speakers) {
				if (s.vendorId != null && s.vendorId != 'new' && s.vendorId != '') {
					Event_Expense_AEU__c e = new Event_Expense_AEU__c();
					e.Estimated__c = s.fee;
					e.Medical_Event_AEU__c = this.event.Id;
					e.Type_AEU__c = 'Speaker Fees';
					//e.Related_Vendor_AEU__c = s.vendorId;
					e.Related_Vendor_AEU__r = new Event_Vendor_AEU__c(External_Id_AEU__c=this.event.Id+';'+s.vendorId);
					//e.Event_Speaker_AEU__c = (Id)s.so.get('Id');
					expensesToInsert.add(e);
				}
			}
			insert expensesToInsert;
		} catch(Exception e) {
			Database.rollback(sp);
			throw e;
		}

		//insert succeeded, send user to event view
		ApexPages.StandardController viewController = new ApexPages.StandardController(this.event);
		PageReference p = viewController.view();
		p.setRedirect(true);
		return p;
	}

	public override List<VendorWrapper> loadVendors(){
		List<VendorWrapper> vendors = new List<VendorWrapper>();
		for (Integer i = 0; i < this.defaultVendorCount; i++) {
			vendors.add(new VendorWrapper('Event_Vendor_AEU__c'));
		}

		return vendors;
	}

	//shows list of ONLY facilitators for this event (either speakers or astellas attendees)
	public List<SelectOption> facilitatorOptions {
		get {
			facilitatorOptions = new List<SelectOption>();
			facilitatorOptions.add(new SelectOption('', '--Select--'));
			//TODO: SET
			//Set<Id> accountIds = new Set<Id>();
			for (GenericSobjectWrapper s : speakers) {
				//if (s.so.get('Speaker_Account_AEU__c') != null)
				//	accountIds.add((Id)s.so.get('Speaker_Account_AEU__c'));
			}
			//TODO: does not pick up this query 
			Map<Id, Account> accountMap = new Map<Id, Account>([Select Id, Name From Account]);

			//Set<Id> userIds = new Set<Id>();
			for (GenericSobjectWrapper a : attendees) {
				//if (a.so.get('User_vod__c') != null)
				//	userIds.add((Id)a.so.get('User_vod__c'));
			}
			Map<Id, User> userMap = new Map<Id, User>([Select Id, Name From User Where Id in :userIds]);

			//Set<Id> speakerAccounts = new Set<Id>();
			for (GenericSobjectWrapper s : speakers) {
				// if (s.so.get('Speaker_Account_AEU__c') != null) {
				// 	if (!speakerAccounts.contains((Id)s.so.get('Speaker_Account_AEU__c'))) {
				// 		String name = accountMap.get((String)s.so.get('Speaker_Account_AEU__c')).Name;
				// 		facilitatorOptions.add(new SelectOption((String)s.so.get('Speaker_Account_AEU__c'), name+' (S)'));
				// 		speakerAccounts.add((Id)s.so.get('Speaker_Account_AEU__c'));
				// 	}
				// }
			}
			for (GenericSobjectWrapper a : attendees) {
				// if (a.so.get('User_vod__c') != null) {
				// 	String name = userMap.get((String)a.so.get('User_vod__c')).Name;
				// 	facilitatorOptions.add(new SelectOption((String)a.so.get('User_vod__c'), name+' (A)'));
				// }
			}
			return facilitatorOptions;
		}
		private set;
	}

	//used on the event expense page
	//shows list of ONLY vendors linked with this event
	public List<SelectOption> eventVendorSelectOptions {
		get {
			eventVendorSelectOptions = new List<SelectOption>();
			eventVendorSelectOptions.add(new SelectOption('', '--Select--'));
			for (VendorWrapper v : vendors) {
				if (v.vendorId != '')
					eventVendorSelectOptions.add(new SelectOption(v.vendorId, v.vendorName));
			}
			return eventVendorSelectOptions;
		}
		private set;
	}

	public PageReference addSpeaker() {
		speakers.add(new Speaker('Event_Speaker_AEU__c'));
		return null;
	}

	public PageReference removeSpeaker() {
		List<Speaker> newSpeakerList = new List<Speaker>();
		for (Speaker sow : speakers) {
			if (sow.hash != deleteHash) {
				newSpeakerList.add(sow);
			}
		}
		speakers = newSpeakerList;
		return null;
	}

	public PageReference addAttendee() {
		attendees.add(new GenericSobjectWrapper('Event_Attendee_vod__c'));
		return null;
	}

	public PageReference removeAttendee() {
		List<GenericSobjectWrapper> newAttendeeList = new List<GenericSobjectWrapper>();
		for (GenericSobjectWrapper sow : attendees) {
			if (sow.hash != deleteHash) {
				newAttendeeList.add(sow);
			}
		}
		attendees = newAttendeeList;
		return null;
	}

	public PageReference addAgendaItem() {
		AgendaItem a = new AgendaItem('Agenda_Item_AEU__c');
		a.so.put('Date_AEU__c', this.event.Start_Date_vod__c);
		a.so.put('Time_Hour_AEU__c', '09');
		a.so.put('Time_Minutes_AEU__c', '00');
		a.index = agendaItems.size()+1;
		agendaItems.add(a);
		return null;
	}

	public PageReference removeAgendaItem() {
		List<AgendaItem> newAgendaList = new List<AgendaItem>();
		for (AgendaItem sow : agendaItems) {
			if (sow.hash != deleteHash) {
				newAgendaList.add(sow);
			}
		}
		agendaItems = newAgendaList;
		return null;
	}

	public PageReference addExpenseItem() {
		expenses.add(new GenericSobjectWrapper('Event_Expense_AEU__c'));
		return null;
	}

	public PageReference removeExpenseitem() {
		List<GenericSobjectWrapper> newExpenseList = new List<GenericSobjectWrapper>();
		for (GenericSobjectWrapper sow : expenses) {
			if (sow.hash != deleteHash) {
				newExpenseList.add(sow);
			}
		}
		expenses = newExpenseList;
		return null;
	}

	public PageReference removeEventVendor() {
		List<VendorWrapper> newVendorList = new List<VendorWrapper>();
		for (VendorWrapper sow : vendors) {
			if (sow.hash != deleteHash) {
				newVendorList.add(sow);
			}
		}
		vendors = newVendorList;
		return null;
	}

	public PageReference addEventVendor() {
		vendors.add(new VendorWrapper('Event_Vendor_AEU__c'));
		return null;
	}

	public List<Speaker> speakers {
		get {
			if (speakers == null) {
				speakers = new List<Speaker>();
				for (Integer i = 0; i < 1; i++) {
					speakers.add(new Speaker('Event_Speaker_AEU__c'));
				}
			}
			return speakers;
		}
		set;
	}

	public List<GenericSobjectWrapper> expenses {
		get {
			if (expenses == null) {
				expenses = new List<GenericSobjectWrapper>();
				for (Integer i = 0; i < 3; i++) {
					expenses.add(new GenericSobjectWrapper('Event_Expense_AEU__c'));
				}
			}
			return expenses;
		}
		set;
	}

	public List<GenericSobjectWrapper> attendees {
		get {
			if (attendees == null) {
				attendees = new List<GenericSobjectWrapper>();
				for (Integer i = 0; i < 3; i++) {
					if (i == 0) {
						GenericSobjectWrapper currentUser = new GenericSobjectWrapper('Event_Attendee_vod__c');
						currentUser.so.put('User_vod__c', UserInfo.getUserId());
						attendees.add(currentUser);
					} else {
						attendees.add(new GenericSobjectWrapper('Event_Attendee_vod__c'));
					}
				}
			}
			return attendees;
		}
		set;
	}

	public List<AgendaItem> agendaItems {
		get {
			//if null, create 3 empty agenda items
			if (agendaItems == null) {
				agendaItems = new List<AgendaItem>();
				for (Integer i = 0; i < 3; i++) {
					AgendaItem agendaItem = new AgendaItem('Agenda_Item_AEU__c');
					agendaItem.so.put('Date_AEU__c', this.event.Start_Date_vod__c);
					agendaItem.so.put('Time_Hour_AEU__c', '09');
					agendaItem.so.put('Time_Minutes_AEU__c', '00');
					agendaItem.index = i+1;
					agendaItems.add(agendaItem);
				}
			}
			agendaItems.sort();
			return agendaItems;
		}
		set;
	}

	//this is erroring because of no setter
	public List<SelectOption> speakerTopics {
		private get {
			List<SelectOption> opts = new List<SelectOption>();
			opts.add(new SelectOption('', '--Select--'));
			opts.add(new SelectOption('', '--New Topic--'));
			for (Speaker_Topic_AEU__c s : [SELECT Id, Name, Title_AEU__c, Additional_Details__c FROM Speaker_Topic_AEU__c WHERE Therapy_Area_AEU__c = :this.event.Therapy_Area_AEU__c AND (Id in :speakerTopicIdsAddedInThisSession OR Approval_Status_AEU__c = 'Approved') ORDER BY Title_AEU__c]) {
				opts.add(new SelectOption(s.Id, s.Title_AEU__c));
			}
			return opts;
		}
	}

	//this is erroring because of no setter
	public List<SelectOption> foodobar {
		set {
			system.debug('foo');
		}
	}

	//this is erroring because of no setter
	public List<SelectOption> foodobar {
		set {
			system.debug('foo');
			for (Integer i = 0; i < 5; i++) {
				system.debug('bar');
			}
		}
		get {
			system.debug('foo');
		}
	}

	public class AgendaItem extends GenericSobjectWrapper implements Comparable {
		public Integer index { get; set; }
		public AgendaItem (String objectAPIName) {
			super (objectAPIName);
		}
		public Integer compareTo(Object compareTo) {
	        AgendaItem item = (AgendaItem) compareTo;
	        if (index == item.index) return 0;
	        if (index > item.index) return 1;
	        return -1;        
	    }
	}

	public class Speaker extends GenericSobjectWrapper {
		public String vendorId { get; set; }
		public String vendorName { get; set; }
		public Decimal fee { get; set; }
		public List<SpeakerTopic> topics { get; set; }
		public Speaker (String objectAPIName) {
			super (objectAPIName);
			this.topics = new List<SpeakerTopic>();
			this.topics.add(new SpeakerTopic());
		}
	}

	public class SpeakerTopic {
		public Id topicId { get; set; }
		public String hash { get; set; }
		public SpeakerTopic() {
			this.hash = AEU_EVENT_UTIL.generateHash(10);
		}
	}

	public PageReference addTopic() {
		Speaker sp;
		for (Speaker s : speakers) {
			if (s.hash == clientHash) {
				sp = s;
				break;
			}
		}
		if (sp != null) {
			for (SpeakerTopic t : sp.topics) {
				if (t.topicId == null) {
					ApexPages.addMessage(new ApexPages.Message(ApexPages.Severity.ERROR, 'Please select a topic'));
					return null;	
				}
			}
			sp.topics.add(new SpeakerTopic());
		}
		return null;
	}

	public PageReference removeTopic() {
		//String speakerHash = clientHash.split(',').get(0); multiple dots deep
		//String topicHash = clientHash.split(',').get(1);

		Speaker sp;
		for (Speaker s : speakers) {
			if (s.hash == speakerHash) {
				sp = s;
				break;
			}
		}

		List<SpeakerTopic> newTopicList = new List<SpeakerTopic>();
		for (SpeakerTopic t : sp.topics) {
			if (t.hash != topicHash) {
				newTopicList.add(t);
			}
		}
		sp.topics = newTopicList;
		return null;
	}

	//inserts a new speaker vendor (approval status=pending)
	public PageReference createSpeakerVendor() {
		try {
			insert newVendor;
			Speaker sp;
			for (Speaker s : speakers) {
				if (s.hash == createHash) {
					sp = s;
					break;
				}
			}
			
			sp.vendorId = newVendor.Id;
			sp.vendorName = newVendor.Name;

			//we set these so we can have them on the client
			this.newVendorId = newVendor.Id;
			this.newVendorName = newVendor.Name; 
			newVendor = new Vendor_AEU__c();
			
		} catch(Exception e) {
			throw e;
		}

		return null;
	}

	@RemoteAction
    global static List<User> getUsersInCurrentUserCountry(String token) {
        try {
        	String currentUserCountry = [Select Astellas_Country_AEU__c From User Where Id = :UserInfo.getUserId()].Astellas_Country_AEU__c;
        	List<User> users = Database.query('SELECT Id, Name FROM User WHERE Name LIKE \'%'+token+'%\' AND Astellas_Country_AEU__c = \''+currentUserCountry+'\'');
        	return users;
        } catch (Exception e) {
        	//return new List<User>{}; does not like this empty
        }
    }

    @RemoteAction
    global static List<Vendor_AEU__c> getSpeakerVendors(String token) {
        List<Vendor_AEU__c> vendors = Database.query('SELECT Id, Name, Address_Line_1_AEU__c, Address_Line_2_AEU__c, City_AEU__c, Post_Code_AEU__c FROM Vendor_AEU__c WHERE (Type_AEU__c = \'Speaker\' or Type_AEU__c = \'Trust\') AND Name LIKE \'%'+token+'%\'');
        return vendors;
    }
}