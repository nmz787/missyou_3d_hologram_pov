function(a0, a1, a2) { // Original name: write, environment: r5
                _fun9439: for(var _fun9439_ip = 0; ; ) switch(_fun9439_ip) {
case 0:
                    r1 = this;
                    r2 = a2;
                    var _closure3_slot0 = r2;
                    var _closure3_slot1 = r1;
                    r2 = r1._pending;
                    if(r2) { _fun9439_ip = 272; continue _fun9439 }
case 28:
                    r2 = r1._destroyed;
                    if(r2) { _fun9439_ip = 272; continue _fun9439 }
case 40:
                    r4 = r1._generateSendBuffer;
                    r3 = a0;
                    r2 = a1;
                    r7 = r4.bind(r1)(r3, r2);
                    var _closure3_slot2 = r7;
                    r3 = r1._writeBufferSize;
                    r2 = r7.byteLength;
                    r2 = r3 + r2;
                    r1['_writeBufferSize'] = r2;
                    r5 = r1._msgId;
                    var _closure3_slot3 = r5;
                    r3 = r1._msgId;
                    r2 = 1;
                    r3 = r3 + r2;
                    r2 = global;
                    r2 = r2.Number;
                    r2 = r2.MAX_SAFE_INTEGER;
                    r2 = r3 % r2;
                    r1['_msgId'] = r2;
                    r4 = function(a0) { // Original name: msgEvtHandler, environment: r0
                        _fun9440: for(var _fun9440_ip = 0; ; ) switch(_fun9440_ip) {
case 0:
                            r0 = a0;
                            r2 = r0.msgId;
                            r3 = r0.err;
                            r1 = _closure3_slot3;
                            if(!(r2 === r1)) { _fun9440_ip = 211; continue _fun9440 }
case 29:
                            r1 = _closure3_slot1;
                            r7 = r1._msgEvtEmitter;
                            r6 = r7.removeListener;
                            r5 = _closure3_slot4;
                            r4 = 'written';
                            r4 = r6.bind(r7)(r4, r5);
                            r5 = r1._writeBufferSize;
                            r4 = _closure3_slot2;
                            r4 = r4.byteLength;
                            r4 = r5 - r4;
                            r1['_writeBufferSize'] = r4;
                            r1['_lastRcvMsgId'] = r2;
                            r4 = r1._resetTimeout;
                            r4 = r4.bind(r1)();
                            r1 = r1.writableNeedDrain;
                            if(!r1) { _fun9440_ip = 151; continue _fun9440 }
case 110:
                            r1 = _closure3_slot1;
                            r1 = r1._lastSentMsgId;
                            if(!(r1 === r2)) { _fun9440_ip = 151; continue _fun9440 }
case 124:
                            r4 = _closure3_slot1;
                            r1 = false;
                            r4['writableNeedDrain'] = r1;
                            r2 = r4.emit;
                            r1 = 'drain';
                            r1 = r2.bind(r4)(r1);
case 151:
                            r1 = _closure3_slot0;
                            if(!r1) { _fun9440_ip = 211; continue _fun9440 }
case 158:
                            r2 = _closure3_slot0;
                            if(r3) { _fun9440_ip = 173; continue _fun9440 }
case 165:
                            r0 = undefined;
                            r0 = r2.bind(r0)();
                            _fun9440_ip = 211; continue _fun9440;
case 173:
                            r0 = global;
                            r0 = r0.Error;
                            r1 = r0.prototype;
                            r1 = Object.create(r1, {constructor: {value: r0}});
                            r10 = r1;
                            r9 = r3;
                            r0 = new r10[r0](r9, r8);
                            r1 = r0 instanceof Object ? r0 : r1;
                            r0 = undefined;
                            r0 = r2.bind(r0)(r1);
case 211:
                            r0 = undefined;
                            return r0;
                        }
                    };
                    var _closure3_slot4 = r4;
                    r3 = r1._msgEvtEmitter;
                    r2 = r3.on;
                    r0 = 'written';
                    r0 = r2.bind(r3)(r0, r4, r1);
                    r2 = r1._writeBufferSize;
                    r0 = r1.writableHighWaterMark;
                    r0 = r2 < r0;
                    if(r0) { _fun9439_ip = 190; continue _fun9439 }
case 182:
                    r2 = true;
                    r1['writableNeedDrain'] = r2;
case 190:
                    r1['_lastSentMsgId'] = r5;
                    r3 = r1._bytesWritten;
                    r2 = r7.byteLength;
                    r2 = r3 + r2;
                    r1['_bytesWritten'] = r2;
                    r2 = _closure1_slot8;
                    r2 = r2.NativeModules;
                    r4 = r2.TcpSockets;
                    r3 = r4.write;
                    r2 = r1._id;
                    r6 = r7.toString;
                    r1 = 'base64';
                    r1 = r6.bind(r7)(r1);
                    r1 = r3.bind(r4)(r2, r1, r5);
                    return r0;
case 272:
                    r0 = global;
                    r2 = r0.Error;
                    r0 = r2.prototype;
                    r1 = Object.create(r0, {constructor: {value: r2}});
                    r10 = 'Socket is closed.';
                    r11 = r1;
                    r0 = new r11[r2](r10, r9);
                    r0 = r0 instanceof Object ? r0 : r1;
                    throw r0;
                }
            }
