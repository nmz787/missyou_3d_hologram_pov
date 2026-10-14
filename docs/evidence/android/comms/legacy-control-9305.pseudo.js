function(a0) { // Original name: playFile, environment: r5
                _fun9305: for(var _fun9305_ip = 0; ; ) switch(_fun9305_ip) {
case 0:
                    r2 = this;
                    r0 = r2.isPlaying;
                    if(r0) { _fun9305_ip = 21; continue _fun9305 }
case 11:
                    r0 = r2.playPlay;
                    r0 = r0.bind(r2)();
case 21:
                    r0 = global;
                    r3 = r0.String;
                    r1 = undefined;
                    r0 = a0;
                    r4 = r3.bind(r1)(r0);
                    r3 = r4.padStart;
                    r1 = 2;
                    r0 = '0';
                    r3 = r3.bind(r4)(r1, r0);
                    r1 = r3.split;
                    r0 = '';
                    r3 = r1.bind(r3)(r0);
                    r1 = r3.map;
                    r0 = function(a0) { // Environment: r0
                        r2 = a0;
                        r1 = r2.charCodeAt;
                        r0 = 0;
                        r0 = r1.bind(r2)(r0);
                        return r0;
                    };
                    r4 = r1.bind(r3)(r0);
                    r1 = r2.send;
                    r0 = 0;
                    r3 = r4[r0];
                    r0 = [99, 51, 49, 99, 52, 48, 97, 98, 101];
                    r0[9] = r3;
                    r3 = 1;
                    r3 = r4[r3];
                    r0[10] = r3;
                    r3 = 97;
                    r0[11] = r3;
                    r4 = 52;
                    r0[12] = r4;
                    r0[13] = r3;
                    r3 = 56;
                    r0[14] = r3;
                    r3 = 99;
                    r0[15] = r3;
                    r3 = 50;
                    r0[16] = r3;
                    r3 = 101;
                    r0[17] = r3;
                    r3 = 51;
                    r0[18] = r3;
                    r0 = r1.bind(r2)(r0);
                    return r0;
                }
            }
