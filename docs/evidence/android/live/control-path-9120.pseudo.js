function(a0) { // Original name: playPause, environment: r5
                _fun9120: for(var _fun9120_ip = 0; ; ) switch(_fun9120_ip) {
case 0:
                    r4 = this;
                    r1 = a0;
                    var _closure3_slot0 = r1;
                    r1 = r4.getIsOldDevice;
                    r1 = r1.bind(r4)();
                    if(r1) { _fun9120_ip = 47; continue _fun9120 }
case 24:
                    r3 = r4.GET;
                    r2 = '/ctrl/play?action=pause';
                    r1 = function(a0, a1) { // Environment: r0
                        _fun9123: for(var _fun9123_ip = 0; ; ) switch(_fun9123_ip) {
case 0:
                            r2 = a0;
                            r0 = a1;
                            r3 = _closure3_slot0;
                            if(!r3) { _fun9123_ip = 47; continue _fun9123 }
case 16:
                            r1 = _closure3_slot0;
                            if(!r2) { _fun9123_ip = 26; continue _fun9123 }
case 23:
                            r2 = r0;
case 26:
                            if(!r2) { _fun9123_ip = 40; continue _fun9123 }
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
                    r1 = r3.bind(r4)(r2, r1);
                    _fun9120_ip = 100; continue _fun9120;
case 47:
                    r1 = _closure1_slot9;
                    r2 = r1.default;
                    r1 = r2.playPause;
                    r3 = r1.bind(r2)();
                    r2 = r3.then;
                    r1 = function(a0) { // Environment: r0
                        _fun9121: for(var _fun9121_ip = 0; ; ) switch(_fun9121_ip) {
case 0:
                            r1 = _closure3_slot0;
                            if(!r1) { _fun9121_ip = 23; continue _fun9121 }
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
                        _fun9122: for(var _fun9122_ip = 0; ; ) switch(_fun9122_ip) {
case 0:
                            r0 = _closure1_slot5;
                            r3 = r0.default;
                            r2 = r3.i;
                            r0 = global;
                            r0 = r0.HermesInternal;
                            r4 = r0.concat;
                            r1 = 'playPause failed error:';
                            r0 = a0;
                            r1 = r4.bind(r1)(r0);
                            r0 = 'ConnectionManager';
                            r0 = r2.bind(r3)(r0, r1);
                            r1 = _closure3_slot0;
                            if(!r1) { _fun9122_ip = 75; continue _fun9122 }
case 62:
                            r2 = _closure3_slot0;
                            r1 = undefined;
                            r0 = false;
                            r0 = r2.bind(r1)(r0);
case 75:
                            r0 = undefined;
                            return r0;
                        }
                    };
                    r0 = r1.bind(r2)(r0);
case 100:
                    r0 = undefined;
                    return r0;
                }
            }
