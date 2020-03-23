/* global */

import Logger from './utils/Logger';

import { EventDispatcher, LicodeEvent } from './Events';

const SocketEvent = (type, specInput) => {
  const that = LicodeEvent({ type });
  that.args = specInput.args;
  return that;
};

/*
 * Class Stream represents a local or a remote Stream in the Room. It will handle the WebRTC
 * stream and identify the stream and where it should be drawn.
 */
const Socket = (newIo) => {
  const that = EventDispatcher();
  const defaultCallback = () => {};
  const messageBuffer = [];

  that.CONNECTED = Symbol('connected');
  that.RECONNECTING = Symbol('reconnecting');
  that.DISCONNECTED = Symbol('disconnected');

  that.state = that.DISCONNECTED;
  that.IO = newIo;

  let socket;

  const emit = (type, ...args) => {
    that.emit(SocketEvent(type, { args }));
  };

  const addToBuffer = (type, message, callback, error) => {
    messageBuffer.push([type, message, callback, error]);
  };

  const flushBuffer = () => {
    if (that.state !== that.CONNECTED) {
      return;
    }
    messageBuffer.forEach((message) => {
      that.sendMessage(...message);
    });
  };

  that.connect = (token, callback = defaultCallback, error = defaultCallback) => {
    const options = {
      reconnect: true,
      reconnectionAttempts: 25,
      secure: token.secure,
      transports: ['websocket']
    };
    const transport = token.secure ? 'wss://' : 'ws://';
    let wsHost = token.host;
    if(wsHost.charAt(wsHost.length - 1) === '/') {
      wsHost = wsHost.substr(0, wsHost.length - 1);
    }
    socket = that.IO.connect(transport + wsHost + '/erizo', options);
    const clientId = token.tokenId;

    socket.on('onAddStream', emit.bind(that, 'onAddStream'));

    socket.on('signaling_message_erizo', emit.bind(that, 'signaling_message_erizo'));
    socket.on('signaling_message_peer', emit.bind(that, 'signaling_message_peer'));
    socket.on('publish_me', emit.bind(that, 'publish_me'));
    socket.on('onBandwidthAlert', emit.bind(that, 'onBandwidthAlert'));

    // We receive an event of new data in one of the streams
    socket.on('onDataStream', emit.bind(that, 'onDataStream'));

    // We receive an event of new data in one of the streams
    socket.on('onUpdateAttributeStream', emit.bind(that, 'onUpdateAttributeStream'));

    // We receive an event of a stream removed from the room
    socket.on('onRemoveStream', emit.bind(that, 'onRemoveStream'));

    // The socket has disconnected
    socket.on('disconnect', (reason) => {
      Logger.debug('disconnect', reason);
      if (reason !== 'io server disconnect' && reason !== 'io client disconnect') {
        that.state = that.RECONNECTING;
        emit('disconnect-pending-reconnect');
        return;
      }
      emit('disconnect', reason);
      socket.close();
    });

    socket.on('connection_failed', (evt) => {
      Logger.error('connection failed');
      emit('connection_failed', evt);
    });
    socket.on('error', (err) => {
      Logger.warning('socket error:', err.message);
      emit('error');
    });
    socket.on('connect_error', (err) => {
      Logger.warning('connect error:', err.message);
    });

    socket.on('connect_timeout', (err) => {
      Logger.warning('connect timeout, error:', err.message);
    });

    socket.on('reconnecting', (attemptNumber) => {
      Logger.debug('reconnecting, attempet:', attemptNumber);
    });

    socket.on('reconnect', (attemptNumber) => {
      Logger.debug('reconnected: attempet:', attemptNumber);
      that.sendMessage('client_reconnect', clientId, () => {
        that.state = that.CONNECTED;
        flushBuffer();
        emit('reconnected');
      }, error);
    });

    socket.on('reconnect_attempt', (attemptNumber) => {
      Logger.debug('reconnect attempt, attempet:', attemptNumber);
    });

    socket.on('reconnect_error', (err) => {
      Logger.debug('error reconnecting, error:', err.message);
    });

    socket.on('reconnect_failed', () => {
      Logger.warning('reconnect failed');
      that.state = that.DISCONNECTED;
      emit('disconnect', 'reconnect failed');
    });

    // First message with the token
    that.sendMessage('token', token, (...args) => {
      that.state = that.CONNECTED;
      callback(...args);
    }, error);
  };

  that.disconnect = () => {
    that.state = that.DISCONNECTED;
    socket.disconnect();
  };

  // Function to send a message to the server using socket.io
  that.sendMessage = (type, msg, callback = defaultCallback, error = defaultCallback) => {
    if (that.state === that.DISCONNECTED && type !== 'token') {
      Logger.error('Trying to send a message over a disconnected Socket');
      return;
    }
    if (that.state === that.RECONNECTING && type !== 'client_reconnect') {
      addToBuffer(type, msg, callback, error);
      return;
    }
    socket.emit(type, msg, (respType, resp) => {
      if (respType === 'success') {
        callback(resp);
      } else if (respType === 'error') {
        error(resp);
      } else {
        callback(respType, resp);
      }
    });
  };

  // It sends a SDP message to the server using socket.io
  that.sendSDP = (type, options, sdp, callback = defaultCallback) => {
    if (that.state === that.DISCONNECTED) {
      Logger.error('Trying to send a message over a disconnected Socket');
      return;
    }
    socket.emit(type, options, sdp, (response, respCallback) => {
      callback(response, respCallback);
    });
  };
  return that;
};

export { SocketEvent, Socket };
