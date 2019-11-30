/*global require, exports, ObjectId*/
'use strict';
var db = require('./dataBase').db;

var logger = require('./../logger').logger;

// Logger
var log = logger.getLogger('RoomRegistry');

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
    var ecId = erizoControllerId + '';
    
    if(!room || !room._id || room._id.length <= 0) {
        if(callback) {
            callback();
        }
        return;
    }
    
    var findECAndUpdateRoom = function(erizoControllerId) {
        db.erizoControllers.findOne({_id: db.ObjectId(erizoControllerId)}, function(err, erizoController) {
            if(err || !erizoController) {
                log.error("Erizo controller not found in db: " + JSON.stringify(err));
                if(callback) {
                    callback();
                }
                return;
            }
            room.erizoControllerId = db.ObjectId(erizoControllerId);
            db.rooms.save(room, function(err) {
               if(err) {
                   log.error("Error in saving the room: " + JSON.stringify(err) + ", room: " + logger.objectToLog(room));
                   if(callback) {
                       callback();
                   }
               } else {
                   callback(erizoController);
               }
            });
        }); 
    };
    
    if (room.erizoControllerId) {
        db.erizoControllers.findOne({_id: db.ObjectId(ecId)}, function(err, erizoController) {
            if(err) {
                log.error("Error in finding Erizo Controller " + ecId + ", " + JSON.stringify(err));
                if(callback) {
                    callback();
                }
                return;
            }
            if(erizoController) {
                return callback(erizoController);
            } else {
                findECAndUpdateRoom(ecId);
            }
        });
    } else {
        findECAndUpdateRoom(ecId);
    }
};

/*
 * Updates a determined room
 */
exports.updateRoom = function (id, room, callback) {
    db.rooms.replaceOne({_id: db.ObjectId(id)}, room, function (error) {
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
