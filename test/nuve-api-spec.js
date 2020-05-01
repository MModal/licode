var assert = require('chai').assert;
var N = require('./nuve'),
	config = require('../licode_config');

var TIMEOUT=10000,
     ROOM_NAME="myTestRoom";

var id;

describe("nuve", function () {
    jasmine.DEFAULT_TIMEOUT_INTERVAL =TIMEOUT;

    beforeEach(function () {
        N.API.init(config.nuve.superserviceID, config.nuve.superserviceKey, 'http://localhost:3000/');
    });

    it("should not list rooms with wrong credentials", function (done) {

        N.API.init("Jose Antonio", config.nuve.superserviceKey, 'http://localhost:3000/');

        N.API.getRooms(function(rooms_) {
            throw "Succeeded and it should fail with bad credentials";
        }, function(error) {
            done();
        });

    });

    it("should create normal rooms", function (done) {
        N.API.createRoom(ROOM_NAME, function(room) {
            id = room._id;
            done();
        }, function(err) {
            throw err;
        });
    });

    it("should list rooms", function (done) {
        N.API.getRooms(function(rooms_) {
            const roomsObj = JSON.parse(rooms_);
            assert.isArray(roomsObj, "This should be an array of rooms");
            done();
        }, function(error) {
            throw error;
        });
    });

    it("should get normal room", function (done) {
        N.API.getRoom(id, function(result) {
            assert.isNotNull(result);
            done();
        }, function(error) {
            throw error;
        });
    });

    it("should get normal room by name", function (done) {
        N.API.getRoomByName(ROOM_NAME, function(result) {
            assert.isNotNull(result);
            done();
        }, function(error) {
            throw error;
        });
    });

    it("should not get normal room by bad name", function (done) {
        N.API.getRoomByName("bad", function(result) {
            throw "Should not have found a room";
        }, function(error) {
            done();
        });
    });

    it("should not get normal room by empty name", function (done) {
        N.API.getRoomByName(null, function(result) {
            throw "Should not have found a room";
        }, function(error) {
            done();
        });
    });

    it("should create tokens for users in normal rooms", function (done) {
        N.API.createToken(id, "user", "presenter", function(token) {
            done();
        }, function(error) {
            throw error;
        });
    });

    it("should create tokens for users with special characters in normal rooms", function (done) {
        N.API.createToken(id, "user_with_$?üóñ", "role", function(token) {
            done();
        }, function(error) {
            throw error;
        });
    });

    it("should get users in normal rooms", function (done) {
        N.API.getUsers(id, function(token) {
            done();
        }, function(error) {
            throw error;
        });
    });

    it("should delete normal rooms", function (done) {
        N.API.deleteRoom(id, function(result) {
            done();
        }, function(error) {
            throw error;
        });

    });

    it("should create p2p rooms", function (done) {
        N.API.createRoom(ROOM_NAME, function(room) {
            id = room._id;
            assert.notEqual(id, undefined, 'Did not provide a valid id');
            done();
        }, function(err) {
            throw err;
        }, {p2p: true});
    });

    it("should get p2p rooms", function (done) {
        N.API.getRoom(id, function(result) {
            done()
        }, function(error) {
            throw error;
        });
    });

    it("should delete p2p rooms", function (done) {
        N.API.deleteRoom(id, function(result) {
            done()
        }, function(error) {
            throw error;
        });
    });
});
