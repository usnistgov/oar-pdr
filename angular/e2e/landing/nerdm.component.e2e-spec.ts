import {browser, element, by, By, $, $$, ExpectedConditions, protractor} from 'protractor';

describe('Nerdm Page', function() {
  beforeEach(async () => {
    return await browser.get('/nerdm');
  });

  it('should display title page', async() => {
    
    var EC = protractor.ExpectedConditions;
    var label = await element(by.css('nerdm-detail p'));
    
    expect(label.getText()).toMatch(/NERDm/i,
      '<P> should say something about NERDM');
   });

});