'use strict';
/*
Params

	room: room to which we need to assing a erizoController.
		{
		name: String,
		[p2p: bool],
		[data: Object],
		_id: ObjectId
		}

	ec_queue: available erizo controllers ordered by priority
		{ erizoControllerId: {
        	ip: String,
        	state: Int,
        	keepAlive: Int,
        	hostname: String,
        	port: Int,
        	ssl: bool
   	 	}, ...}

Returns

	erizoControler: the erizo controller selected from ecQueue

*/

var i = -1;

exports.getErizoController = function (room, ecQueue) {
  i = i < ecQueue.length - 1 ? i + 1 : 0;     
  var erizoController = ecQueue[i];
  return erizoController;
};
