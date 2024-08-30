import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BrowserAnimationsModule} from '@angular/platform-browser/animations';
import { ResultitemComponent } from './resultitem.component';

describe('ResultitemComponent', () => {
  let component: ResultitemComponent;
  let fixture: ComponentFixture<ResultitemComponent>;
  let resultItem = {
    "_id": {
      "timestamp": 1724428246,
      "date": "2024-08-23T15:50:46.000+00:00"
    },
    "landingPage": "https://www.ctcms.nist.gov/~knc6/JARVIS.html",
    "@type": [
      "nrdp:PublicDataResource"
    ],
    "description": [
      "JARVIS (Joint Automated Repository for Various Integrated Simulations) is a repository designed to automate materials discovery using classical force-field, density functional theory, machine learning calculations and experiments.The Force-field section of JARVIS (JARVIS-FF) consists of thousands of automated LAMMPS based force-field calculations on DFT geometries. Some of the properties included in JARVIS-FF are energetics, elastic constants, surface energies, defect formations energies and phonon frequencies of materials.The Density functional theory section of JARVIS (JARVIS-DFT) consists of thousands of VASP based calculations for 3D-bulk, single layer (2D), nanowire (1D) and molecular (0D) systems. Most of the calculations are carried out with optB88vDW functional. JARVIS-DFT includes materials data such as: energetics, diffraction pattern, radial distribution function, band-structure, density of states, carrier effective mass, temperature and carrier concentration dependent thermoelectric properties, elastic constants and gamma-point phonons.The Machine-learning section of JARVIS (JARVIS-ML) consists of machine learning prediction tools, trained on JARVIS-DFT data. Some of the ML-predictions focus on energetics, heat of formation, GGA/METAGGA bandgaps, bulk and shear modulus."
    ],
    "ediid": "5BD81D0B67AA9AFAE0531A57068100201871",
    "title": "JARVIS: Joint Automated Repository for Various Integrated Simulations",
    "active": true,
    "isExpanded": false
  };
  let colorScheme = {"default":"#003c97","light":"#e3efff","lighter":"#f7f7fa","dark":"#00076c","hover":"#ffffff"};

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ResultitemComponent ],
      imports: [ BrowserAnimationsModule ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ResultitemComponent);
    component = fixture.componentInstance;
    component.resultItem = resultItem;
    component.colorScheme = colorScheme;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
