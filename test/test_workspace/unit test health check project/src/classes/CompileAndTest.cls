@isTest
private class CompileAndTest {
	@isTest static void test_method_one() {
		// Implement test code
		Database.query('Select foo from bar');
	}
	
	@isTest static void test_method_two() {
		// Implement test code
		Account a = [SELECT ID FROM Account];
	}

}