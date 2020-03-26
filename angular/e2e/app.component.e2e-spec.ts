import {browser, element, by, By, $, $$, ExpectedConditions, protractor} from 'protractor';

describe('App Page', function() {

  it('should open about page', function() {
    // expect(true).toBe(true);
    browser.get('/pdr/about');
    browser.waitForAngular();
    var label = element.all(by.css('label'));

    expect(label.get(0).getText()).toContain('About Public Data Repository');
    // expect<any>(browser.getCurrentUrl()).toEqual('/about');
  });

  it('should open sample page', function() {
    browser.get('/od/id/SAMPLE123456');
    //browser.waitForAngular();
    var EC = protractor.ExpectedConditions;
    var label = element.all(by.css('h2'));

    expect(label.get(0).getText()).toContain('Measurement of the Behavior of Steel Beams under Localized Fire Exposure');
   });

  // it('should check contents of the P field', function() {
  //   browser.get('#/home');
  //   browser.waitForAngular();
  //   // var EC = protractor.ExpectedConditions;
  //   // var list = element.all(by.css('p'));
    
  // });

});