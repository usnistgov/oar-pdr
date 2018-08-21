import {browser, element, by, By, $, $$, ExpectedConditions, protractor} from 'protractor';

describe('About Page', function() {

  beforeEach(async () => {
    //browser.waitForAngular();
    return await browser.get('/about');
  });

  it('should display title of about page', async() => {

    var EC = protractor.ExpectedConditions;
    var label = await element(by.css('.labelStyle'));

    expect(label.getText()).toContain('About Public Data Repository');
   });

});
