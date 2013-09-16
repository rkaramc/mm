trigger MYCOOLTRIGGER on Opportunity (before insert, before update) {
	Account a = [select id from account limit 1];
	for (Integer i = 0; i < 10; i++) {
		Account a = [Select ID From Account Where Name != 'foo'];
		//foo(trigger.oldmap.get('Id'));
		foo.bar.bat.foo(bar);
		trigger.newmap.get('foo').bar;
		//String.do_something(bar);
	}
}