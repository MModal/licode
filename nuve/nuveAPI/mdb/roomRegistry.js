/*global require, exports, ObjectId*/
'use strict';
var db = require('./dataBase').db;

var logger = require('./../logger').logger;

// Logger
var log = logger.getLogger('RoomRegistry');

var makePromise = function(fn, params) {
    return new Promise(function(resolve, reject) {
       fn(params, function(err, value) {
           if(err) {
               reject(err);
            } else {
                resolve(value);
            }
        }); 
    });
};

exports.getRooms = function (callback) {
    db.rooms.find({}).toArray(function (err, rooms) {
        if (err || !rooms) {
            log.info('message: rooms list empty');
        } else {
            callback(rooms);
        }
    });
};

var getRoom = exports.getRoom = function (id, callback) {
    db.rooms.findOne({_id: db.ObjectId(id)}, function (err, room) {
        if (room === undefined) {
            log.warn('message: getRoom - Room not found, roomId: ' + id);
        }
        if (callback !== undefined) {
            callback(room);
        }
    });
};

var hasRoom = exports.hasRoom = function (id, callback) {
    getRoom(id, function (room) {
        if (room === undefined) {
            callback(false);
        } else {
            callback(true);
        }
    });
};

/*
 * Adds a new room to the data base.
 */
exports.addRoom = function (room, callback) {
    db.rooms.save(room, function (error, saved) {
        if (error) log.warn('message: addRoom error, ' + logger.objectToLog(error));
        callback(saved);
    });
};

exports.assignErizoControllerToRoom = function(room, erizoControllerId, callback) {
    const _roomId = room._id + '';
    const _erizoContollerId = erizoControllerId + '';
    console.log("Starting the process of EC assign to room", _roomId, _erizoContollerId);
    var foundRoom;
    
    makePromise(db.rooms.findOne, {_id: new db.ObjectId(_roomId)}).then(function(room) {
        console.log("Found room with id", room);
        foundRoom = room;
        if(room && room.erizoControllerId) {
            return makePromise(db.erizoControllers.findOne, {_id: room.erizoControllerId});
        } else {
            return Promise.resolve();
        }
    }).then(function(erizoController) {
        if(foundRoom) {
            console.log("Found EC for room in db", erizoController);
            if(erizoController) {
                if(callback) {
                    callback(erizoController);
                }
            } else {
                return makePromise(db.erizoControllers.findOne, {_id: new db.ObjectId(_erizoControllerId)});
            }
        } 
        return Promise.resolve();
    }).then(function(erizoController) {
        console.log("Located EC in db", erizoController);
        if(foundRoom && erizoController) {
            console.log("Will save room", foundRoom);
            foundRoom.erizoControllerId = new db.ObjectId(_erizoControllerId);
            makePromise(db.rooms.save, foundRoom).then(function() {
                if(callback) {
                    callback(erizoController);   
                }
            }).catch(function(error) {
                console.error('assignErizoControllerToRoom save room error', error);
                log.warn('message: assignErizoControllerToRoom save room error, ' + logger.objectToLog(error));
                if(callback) {
                    callback();
                }
            });
        }
    }).catch(function(error) {
        console.error('assignErizoControllerToRoom room error', error);
        log.warn('message: assignErizoControllerToRoom room error, ' + logger.objectToLog(error));
        if(callback) {
            callback();
        }
    });
};

/*
 * Updates a determined room
 */
exports.updateRoom = function (id, room, callback) {
    db.rooms.update({_id: db.ObjectId(id)}, room, function (error) {
        if (error) log.warn('message: updateRoom error, ' + logger.objectToLog(error));
        if (callback) callback(error);
    });
};

/*
 * Removes a determined room from the data base.
 */
exports.removeRoom = function (id) {
    hasRoom(id, function (hasR) {
        if (hasR) {
            db.rooms.remove({_id: db.ObjectId(id)}, function (error) {
                if (error) log.warn('message: removeRoom error, ' +
                   logger.objectToLog(error));
            });
        }
    });
};
