import {browser, element, by, By, $, $$, ExpectedConditions, protractor} from 'protractor';

describe('Noid Page', function() {
  
  beforeEach(async () => {
    return await browser.get('/id');
  });

  it('should display title page', async() => {
    
    var EC = protractor.ExpectedConditions;
    var label = await element(by.css('noid-template h3'));
    
    expect(label.getText()).toMatch(/empty/i,
      '<h3> should say something about empty page');
  });

});