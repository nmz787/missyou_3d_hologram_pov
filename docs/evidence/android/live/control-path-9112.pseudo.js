function(a0, a1) { // Original name: playFile, environment: r5
                _fun9112: for(var _fun9112_ip = 0; ; ) switch(_fun9112_ip) {
case 0:
                    r1 = a0;
                    r6 = this;
                    r2 = a1;
                    var _closure3_slot0 = r2;
                    r3 = r1.index;
                    r7 = r1.name;
                    var _closure3_slot1 = r7;
                    r1 = r6.getIsOldDevice;
                    r2 = r1.bind(r6)();
                    if(r2) { _fun9112_ip = 110; continue _fun9112 }
case 44:
                    r5 = r6.GET;
                    r2 = _closure1_slot7;
                    r4 = r2.default;
                    r2 = r4.encodeGBKToHexString;
                    r8 = r2.bind(r4)(r7);
                    r2 = global;
                    r2 = r2.HermesInternal;
                    r7 = r2.concat;
                    r4 = '/DCIM/';
                    r2 = '?act=play';
                    r4 = r7.bind(r4)(r8, r2);
                    r2 = function(a0, a1) { // Environment: r0
                        _fun9115: for(var _fun9115_ip = 0; ; ) switch(_fun9115_ip) {
case 0:
                            r2 = a0;
                            r0 = a1;
                            r3 = _closure3_slot0;
                            if(!r3) { _fun9115_ip = 47; continue _fun9115 }
case 16:
                            r1 = _closure3_slot0;
                            if(!r2) { _fun9115_ip = 26; continue _fun9115 }
case 23:
                            r2 = r0;
case 26:
                            if(!r2) { _fun9115_ip = 40; continue _fun9115 }
case 29:
                            r3 = r0.code;
                            r0 = 0;
                            r2 = r3 === r0;
case 40:
                            r0 = undefined;
                            r0 = r1.bind(r0)(r2);
case 47:
                            r0 = undefined;
                            return r0;
                        }
                    };
                    r2 = r5.bind(r6)(r4, r2);
                    _fun9112_ip = 161; continue _fun9112;
case 110:
                    r1 = _closure1_slot9;
                    r2 = r1.default;
                    r1 = r2.playFile;
                    r3 = r1.bind(r2)(r3);
                    r2 = r3.then;
                    r1 = function(a0) { // Environment: r0
                        _fun9113: for(var _fun9113_ip = 0; ; ) switch(_fun9113_ip) {
case 0:
                            r1 = _closure3_slot0;
                            if(!r1) { _fun9113_ip = 23; continue _fun9113 }
case 10:
                            r2 = _closure3_slot0;
                            r1 = undefined;
                            r0 = true;
                            r0 = r2.bind(r1)(r0);
case 23:
                            r0 = undefined;
                            return r0;
                        }
                    };
                    r2 = r2.bind(r3)(r1);
                    r1 = r2.catch;
                    r0 = function(a0) { // Environment: r0
                        _fun9114: for(var _fun9114_ip = 0; ; ) switch(_fun9114_ip) {
case 0:
                            r0 = _closure1_slot5;
                            r4 = r0.default;
                            r3 = r4.i;
                            r7 = _closure3_slot1;
                            r1 = global;
                            r1 = r1.HermesInternal;
                            r6 = r1.concat;
                            r5 = 'playFile ';
                            r2 = ' failed error:';
                            r1 = a0;
                            r2 = r6.bind(r5)(r7, r2, r1);
                            r1 = 'ConnectionManager';
                            r1 = r3.bind(r4)(r1, r2);
                            r1 = _closure3_slot0;
                            if(!r1) { _fun9114_ip = 85; continue _fun9114 }
case 72:
                            r2 = _closure3_slot0;
                            r1 = undefined;
                            r0 = false;
                            r0 = r2.bind(r1)(r0);
case 85:
                            r0 = undefined;
                            return r0;
                        }
                    };
                    r0 = r1.bind(r2)(r0);
case 161:
                    r0 = undefined;
                    return r0;
                }
            }
