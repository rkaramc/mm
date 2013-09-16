public with sharing class MultiselectExampleController {

    public SelectOption[] selectedContacts { get; set; }
    public SelectOption[] allContacts { get; set; }
    
    public String foo { 
        get{
            String foo = 'bar';
            for ( Integer i=0; i<5; i++) {
                system.debug('foo');
            }
        } 

        private set;
    }

    public String message { 
        get {
            String foo = 'bar';
        } 

        set {
            String goo = 'bat'; 
            for ( Integer i=0; i<5; i++) {
                system.debug('foo');
            }
        }
    }
    
    public MultiselectExampleController() {
        selectedContacts = new List<SelectOption>();
        
        List<Contact> contacts = [SELECT Name, Id FROM Contact];    
        allContacts = new List<SelectOption>();
        for ( Contact c : contacts ) {
            allContacts.add(new SelectOption(c.Id, c.Name));
        }
    }

    public void nooooo() {

    }

    public PageReference save() {
        message = 'Selected \'foo\' Contacts: ';
        Boolean first = true;
        for ( SelectOption so : selectedContacts ) {
            if (!first) {
                message += ', ';
            }
            message += so.getLabel() + ' (' + so.getValue() + ')';
            first = false;
        }
        Account a = [Select Id FROM Account];
        return null;       
    }

    public void doSomethingCool() {
        Contact c = [Select ID FRom Contact WHERE Name = 'foo'];
    }
}