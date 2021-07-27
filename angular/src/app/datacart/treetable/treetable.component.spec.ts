import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { CartTreeNode, TreetableComponent } from './treetable.component';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { CartService } from '../../datacart/cart.service';
import { DataCartItem, DataCart } from '../../datacart/cart';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestDataService } from '../../shared/testdata-service/testDataService';
import { TreeTableModule } from 'primeng/treetable';

describe('CartTreeNode', () => {
    it('constructor', () => {
        let node = new CartTreeNode();
        expect(node.children).toEqual([]);
        expect(node.isExpanded).toBeFalsy();
        expect(node.data.key).toEqual('');
        expect(node.data.name).toEqual('');
        expect(node.data.size).toEqual('');
        expect(node.data.mediaType).toEqual('');
        expect(node.data.resTitle).toEqual('');
        expect(node.data.zipFile).toEqual('');
        expect(node.data.message).toEqual('');
        expect(node.data.filetype).toEqual("Subcollection");
        expect(node.data.cartItem).toBeNull();

        node = new CartTreeNode('goob');
        expect(node.children).toEqual([]);
        expect(node.isExpanded).toBeFalsy();
        expect(node.data.key).toEqual('goob');
        expect(node.data.name).toEqual('goob');
        expect(node.data.resTitle).toEqual('');

        node = new CartTreeNode('goob', 'foo');
        expect(node.children).toEqual([]);
        expect(node.isExpanded).toBeFalsy();
        expect(node.data.key).toEqual('foo');
        expect(node.data.name).toEqual('goob');
        expect(node.data.resTitle).toEqual('');

        node = new CartTreeNode('goob', 'foo', "Duke");
        expect(node.children).toEqual([]);
        expect(node.isExpanded).toBeFalsy();
        expect(node.data.key).toEqual('foo');
        expect(node.data.name).toEqual('goob');
        expect(node.data.resTitle).toEqual('Duke');
    });

    it('upsertNodeFor()', () => {
        let dc: DataCart = DataCart.createCart("goob");
        dc.addFile("foo", { filePath: "readme",   resTitle: "All About Foo", downloadURL: "http://here", size: 12536 });
        dc.addFile("foo", { filePath: "bar/goo",  resTitle: "All About Foo", downloadURL: "http://here", size: 54 });
        dc.addFile("foo", { filePath: "bar/good", resTitle: "All About Foo", downloadURL: "http://here", size: 12536111 });

        let node: CartTreeNode = new CartTreeNode();
        let item: DataCartItem = dc.findFile("foo", "readme");
        node.upsertNodeFor(item);
        expect(node.children.length).toEqual(1);
        expect(node.data.cartItem).toBeNull();
        expect(node.children[0].data.key).toEqual("foo");
        expect(node.children[0].data.resTitle).toEqual("All About Foo");
        expect(node.children[0].data.name).toEqual("foo");
        expect(node.children[0].keyname).toEqual("foo");
        expect(node.children[0].children.length).toEqual(1);
        expect(node.children[0].children[0].data.key).toEqual("foo/readme");
        expect(node.children[0].children[0].data.resTitle).toEqual("All About Foo");
        expect(node.children[0].children[0].data.name).toEqual("readme");
        expect(node.children[0].children[0].keyname).toEqual("readme");
        expect(node.children[0].children[0].data.cartItem).toBe(item);
        expect(node.children[0].children[0].data.size).toEqual("12.5 kB");
        expect(node.children[0].children[0].children.length).toEqual(0);

        item = dc.findFile("foo", "bar/goo");
        node.upsertNodeFor(item);
        expect(node.children.length).toEqual(1);
        expect(node.data.cartItem).toBeNull();
        expect(node.children[0].data.key).toEqual("foo");
        expect(node.children[0].children.length).toEqual(2);
        expect(node.children[0].children[0].data.key).toEqual("foo/readme");
        expect(node.children[0].children[0].data.resTitle).toEqual("All About Foo");
        expect(node.children[0].children[0].data.name).toEqual("readme");
        expect(node.children[0].children[1].data.key).toEqual("foo/bar");
        expect(node.children[0].children[1].data.resTitle).toEqual("All About Foo");
        expect(node.children[0].children[1].data.name).toEqual("bar");
        expect(node.children[0].children[1].data.cartItem).toBeNull();
        expect(node.children[0].children[1].children.length).toEqual(1);
        expect(node.children[0].children[1].children[0].data.key).toEqual("foo/bar/goo");
        expect(node.children[0].children[1].children[0].data.resTitle).toEqual("All About Foo");
        expect(node.children[0].children[1].children[0].data.name).toEqual("goo");
        expect(node.children[0].children[1].children[0].keyname).toEqual("goo");
        expect(node.children[0].children[1].children[0].data.cartItem).toBe(item);
        expect(node.children[0].children[1].children[0].data.size).toEqual("54 Bytes");
        expect(node.children[0].children[1].children[0].children.length).toEqual(0);

        item = dc.findFile("foo", "bar/good");
        node.upsertNodeFor(item);
        expect(node.children.length).toEqual(1);
        expect(node.data.cartItem).toBeNull();
        expect(node.children[0].data.key).toEqual("foo");
        expect(node.children[0].children.length).toEqual(2);
        expect(node.children[0].children[0].data.key).toEqual("foo/readme");
        expect(node.children[0].data.resTitle).toEqual("All About Foo");
        expect(node.children[0].children[0].data.name).toEqual("readme");
        expect(node.children[0].children[1].data.key).toEqual("foo/bar");
        expect(node.children[0].children[1].data.resTitle).toEqual("All About Foo");
        expect(node.children[0].children[1].data.name).toEqual("bar");
        expect(node.children[0].children[1].data.cartItem).toBeNull();
        expect(node.children[0].children[1].children.length).toEqual(2);
        expect(node.children[0].children[1].children[0].data.key).toEqual("foo/bar/goo");
        expect(node.children[0].children[1].children[0].data.resTitle).toEqual("All About Foo");
        expect(node.children[0].children[1].children[0].data.name).toEqual("goo");
        expect(node.children[0].children[1].children[1].data.key).toEqual("foo/bar/good");
        expect(node.children[0].children[1].children[1].data.resTitle).toEqual("All About Foo");
        expect(node.children[0].children[1].children[1].data.name).toEqual("good");
        expect(node.children[0].children[1].children[1].keyname).toEqual("good");
        expect(node.children[0].children[1].children[1].data.cartItem).toBe(item);
        expect(node.children[0].children[1].children[1].data.size).toEqual("12.5 MB");
        expect(node.children[0].children[1].children[1].data.zipFile).toEqual('');

        // now to an update
        item.zipFile = "goob.zip";
        node.upsertNodeFor(item);
        expect(node.children[0].children[1].children[1].data.size).toEqual("12.5 MB");
        expect(node.children[0].children[1].children[1].data.zipFile).toEqual('goob.zip');
    });

    it('findNode()', () => {
        let dc: DataCart = DataCart.createCart("goob");
        dc.addFile("foo", { filePath: "readme",   resTitle: "All About Foo", downloadURL: "http://here" });
        dc.addFile("foo", { filePath: "bar/goo",  resTitle: "All About Foo", downloadURL: "http://here" });
        dc.addFile("foo", { filePath: "bar/good", resTitle: "All About Foo", downloadURL: "http://here" });

        let node: CartTreeNode = new CartTreeNode();
        node.upsertNodeFor(dc.findFile("foo", "readme"));
        node.upsertNodeFor(dc.findFile("foo", "bar/goo"));
        node.upsertNodeFor(dc.findFile("foo", "bar/good"));

        let nd: CartTreeNode = node.findNode("foo/bar");
        expect(nd).not.toBeNull();
        expect(nd.data.key).toEqual("foo/bar");
        expect(nd.keyname).toEqual("bar");
        expect(nd.data.cartItem).toBeNull();

        nd = node.findNode("foo/bar/good");
        expect(nd).not.toBeNull();
        expect(nd.data.key).toEqual("foo/bar/good");
        expect(nd.keyname).toEqual("good");
        expect(nd.data.cartItem).not.toBeNull();
    });

    it('cleanNodes()', () => {
        let dc: DataCart = DataCart.createCart("goob");
        dc.addFile("foo", { filePath: "readme",   resTitle: "All About Foo", downloadURL: "http://here" });
        dc.addFile("foo", { filePath: "bar/goo",  resTitle: "All About Foo", downloadURL: "http://here" });
        dc.addFile("foo", { filePath: "bar/good", resTitle: "All About Foo", downloadURL: "http://here" });

        let node: CartTreeNode = new CartTreeNode();
        node.upsertNodeFor(dc.findFile("foo", "readme"));
        node.upsertNodeFor(dc.findFile("foo", "bar/goo"));
        node.upsertNodeFor(dc.findFile("foo", "bar/good"));

        expect(node.findNode("foo")).not.toBeNull();
        expect(node.findNode("foo/bar")).not.toBeNull();
        expect(node.findNode("foo/bar/goo")).not.toBeNull();

        expect(dc.removeFileById("foo", "bar/goo")).toBeTruthy();
        expect(dc.removeFileById("foo", "bar/good")).toBeTruthy();
        node.cleanNodes(dc);
        expect(node.findNode("foo/bar/goo")).toBeNull();
        expect(node.findNode("foo/bar/good")).toBeNull();
        expect(node.findNode("foo/bar")).toBeNull();
        expect(node.findNode("foo")).not.toBeNull();
    });
});

describe('TreetableComponent', () => {
  let component: TreetableComponent;
  let fixture: ComponentFixture<TreetableComponent>;

  beforeEach(async(() => {
    let dc: DataCart = DataCart.openCart("goob");
    dc._forget();
    dc.addFile("foo", { filePath: "bar/goo",  count: 3, downloadURL: "http://here", resTitle: "fooishness" },
               false, false);
    dc.addFile("foo", { filePath: "bar/good", count: 3, downloadURL: "http://here", resTitle: "fooishness" },
               false, false);
    dc.addFile("foo", { filePath: "readme", count: 3, downloadURL: "http://here", resTitle: "fooishness" },
               false, false);
    dc.save();
    
    TestBed.configureTestingModule({
      declarations: [ TreetableComponent ],
      schemas: [NO_ERRORS_SCHEMA],
      imports: [
        TreeTableModule,
        HttpClientTestingModule],
      providers: [
        CartService,
        DownloadService,
        TestDataService,
        GoogleAnalyticsService]
    })
    .compileComponents();
  }));

  beforeEach(async(() => {
    fixture = TestBed.createComponent(TreetableComponent);
    component = fixture.componentInstance;
    component.cartName = "goob";
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
    expect(component.dataTree.children.length).toBe(1);
    expect(component.dataTree.children[0].data.name).toBe("fooishness");
    expect(component.dataTree.children[0].children.length).toEqual(2);
    expect(component.dataTree.children[0].children[0].data.name).toEqual("bar");
    expect(component.dataTree.children[0].children[0].children.length).toBe(2);
    expect(component.dataTree.children[0].children[0].children[0].data.name).toEqual("goo");
    expect(component.dataTree.children[0].children[0].children[1].data.name).toEqual("good");
    expect(component.dataTree.children[0].children[1].data.name).toEqual("readme");
  });
});
