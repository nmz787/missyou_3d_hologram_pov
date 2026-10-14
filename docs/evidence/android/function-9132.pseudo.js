function(a0) { // Original name: _handleDeviceFileList, environment: r5
                _fun9132: for(var _fun9132_ip = 0; ; ) switch(_fun9132_ip) {
case 0:
                    r4 = a0;
                    r2 = this;
                    var _closure3_slot0 = r2;
                    r0 = null;
                    if(!(r4 != r0)) { _fun9132_ip = 60; continue _fun9132 }
case 17:
                    r0 = undefined;
                    if(!(r4 != r0)) { _fun9132_ip = 60; continue _fun9132 }
case 23:
                    r3 = r4.map;
                    r1 = function(a0) { // Environment: r1
                        _fun9133: for(var _fun9133_ip = 0; ; ) switch(_fun9133_ip) {
case 0:
                            r4 = a0;
                            r2 = r4.name;
                            r1 = r2.match;
                            r0 = /^(.{2})[-_](.*)\.bin$/;
                            r2 = r1.bind(r2)(r0);
                            r0 = r4.name;
                            if(r2) { _fun9133_ip = 89; continue _fun9133 }
case 40:
                            r5 = r4.name;
                            r3 = r5.endsWith;
                            r1 = '.bin';
                            r1 = r3.bind(r5)(r1);
                            if(!r1) { _fun9133_ip = 158; continue _fun9133 }
case 63:
                            r6 = r4.name;
                            r5 = r6.slice;
                            r3 = 0;
                            r1 = -4;
                            r0 = r5.bind(r6)(r3, r1);
                            _fun9133_ip = 158; continue _fun9133;
case 89:
                            r1 = 1;
                            r5 = r2[r1];
                            r7 = r2[r1];
                            r1 = 2;
                            r6 = r2[r1];
                            r1 = global;
                            r1 = r1.HermesInternal;
                            r3 = r1.concat;
                            r2 = '';
                            r1 = '.';
                            r0 = r3.bind(r2)(r7, r1, r6);
                            r2 = _closure3_slot0;
                            r3 = r2.usedIdentifierSet;
                            r2 = r3.add;
                            r2 = r2.bind(r3)(r5);
case 158:
                            r1 = global;
                            r3 = r1.Object;
                            r2 = r3.assign;
                            r1 = {};
                            r1['displayName'] = r0;
                            r0 = {};
                            r0 = r2.bind(r3)(r0, r4, r1);
                            return r0;
                        }
                    };
                    r3 = r3.bind(r4)(r1);
                    r1 = r2.onFileListChangedBlock;
                    if(!r1) { _fun9132_ip = 58; continue _fun9132 }
case 47:
                    r1 = r2.onFileListChangedBlock;
                    r1 = r1.bind(r2)(r3);
case 58:
                    return r0;
case 60:
                    r0 = r2.onFileListChangedBlock;
                    if(!r0) { _fun9132_ip = 84; continue _fun9132 }
case 69:
                    r1 = r2.onFileListChangedBlock;
                    r0 = new Array(0);
                    r0 = r1.bind(r2)(r0);
case 84:
                    r0 = undefined;
                    return r0;
                }
            }
