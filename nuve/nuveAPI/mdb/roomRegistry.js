/*global require, exports, ObjectId*/
'use strict';
var db = require('./dataBase').db;

var logger = require('./../logger').logger;

var erizoControllerRegistry = require('./erizoControllerRegistry');

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

exports.getRoomsForService = function (serviceId, callback) {
    db.rooms.find({service: db.ObjectId(serviceId)}).toArray(function (err, rooms) {
        if (err || !rooms) {
            log.warn(`warn: getRoomsForService rooms not found for ${serviceId}. Error: ${logger.objectToLog(err)}`);
            rooms = [];
        }
        callback(rooms);
    });
};

exports.getRoomForService = function (id, serviceId, callback) {
    db.rooms.findOne({_id: db.ObjectId(id), service: db.ObjectId(serviceId)}, function (err, room) {
        if (err || !room) {
            log.warn(`warn: getRoomForService room not found with id ${id} for ${serviceId}. Error: ${logger.objectToLog(err)}`);
            room = undefined;
        } else {
            log.info(`message: getRoomForService found room ${JSON.stringify(room)} for id ${id} and service ${serviceId}`);
        }
        callback(room);
    });
};

exports.getRoomByNameForService = function (name, serviceId, callback) {
    db.rooms.findOne({name: name, service: db.ObjectId(serviceId)}, function (err, room) {
        if (err || !room) {
            log.warn(`warn: getRoomByNameForService room not found with name ${name} for ${serviceId}. Error: ${logger.objectToLog(err)}`);
            room = undefined;
        } else {
            log.info(`message: getRoomByNameForService found room ${JSON.stringify(room)} for name ${name} and service ${serviceId}`);
        }
        callback(room);
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
exports.addRoom = function (room, service, callback) {
    room.service = db.ObjectId(service._id);
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
        erizoControllerRegistry.getErizoController(erizoControllerId, function(erizoController) {
            if(!erizoController) {
                log.error("Erizo controller not found in db" + erizoControllerId);
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
                   console.log(`Assigned EC ${erizoController._id} to the room ${JSON.stringify(room)}`);
                   callback(erizoController);
               }
            });
        });
    };
    
    if (room.erizoControllerId) {
        erizoControllerRegistry.getErizoController(ecId, function (erizoController) {
            if(erizoController) {
                console.log(`Found EC ${erizoController._id} for the room ${JSON.stringify(room)}`);
                callback(erizoController);
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

exports.removeRoomsForService = function (serviceId) {
    db.rooms.remove({service: db.ObjectId(serviceId)}, function (error) {
        if (error) log.warn('message: removeRoomsForService error, ' + logger.objectToLog(error));
    });
};
