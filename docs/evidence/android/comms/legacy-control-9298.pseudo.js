function* (a0) { // Original name: ?anon_0_, environment: r0
                        _fun9298: for(var _fun9298_ip = 0; ; ) switch(_fun9298_ip) {
case 0:
                            StartGenerator();
                            r1 = a0;
                            r4 = this;
                            ResumeGenerator(result_out_reg=0, return_bool_out_reg=5);
                            if(r5) { _fun9298_ip = 341; continue _fun9298 }
case 17:
                            r7 = r1;
                            var _closure5_slot0 = r1;
                            r6 = undefined;
                            r2 = undefined;
case 28: // try_start_0
                            r1 = global;
                            r5 = r1.String;
                            r10 = r7;
                            r8 = r5.bind(r6)(r10);
                            r7 = r8.padStart;
                            r6 = 2;
                            r5 = '0';
                            r6 = r7.bind(r8)(r6, r5);
                            r5 = _closure1_slot5;
                            r8 = r5.default;
                            r7 = r8.i;
                            r1 = r1.HermesInternal;
                            r9 = r1.concat;
                            r5 = 'Delete file index: ';
                            r1 = ', str: ';
                            r5 = r9.bind(r5)(r10, r1, r6);
                            r1 = 'TCPClient';
                            r1 = r7.bind(r8)(r1, r5);
                            r5 = r6.split;
                            r1 = '';
                            r6 = r5.bind(r6)(r1);
                            r5 = r6.map;
                            r1 = function(a0) { // Environment: r3
                                r2 = a0;
                                r1 = r2.charCodeAt;
                                r0 = 0;
                                r0 = r1.bind(r2)(r0);
                                return r0;
                            };
                            r7 = r5.bind(r6)(r1);
                            r5 = r4.send;
                            r1 = 0;
                            r6 = r7[r1];
                            r1 = [99, 51, 49, 99, 51, 57, 97, 98, 101];
                            r1[9] = r6;
                            r6 = 1;
                            r6 = r7[r6];
                            r1[10] = r6;
                            r6 = 97;
                            r1[11] = r6;
                            r7 = 52;
                            r1[12] = r7;
                            r1[13] = r6;
                            r6 = 56;
                            r1[14] = r6;
                            r6 = 99;
                            r1[15] = r6;
                            r6 = 50;
                            r1[16] = r6;
                            r6 = 101;
                            r1[17] = r6;
                            r6 = 51;
                            r1[18] = r6;
                            r1 = r5.bind(r4)(r1);
                            SaveGenerator(address=241);
case 239:
                            return r1;
case 241:
                            ResumeGenerator(result_out_reg=1, return_bool_out_reg=5);
                            if(r5) { _fun9298_ip = 334; continue _fun9298 }
case 247:
                            r6 = r4.fileList;
                            r5 = r6.filter;
                            r3 = function(a0) { // Environment: r3
                                r0 = a0;
                                r1 = r0.index;
                                r0 = _closure5_slot0;
                                r0 = r1 !== r0;
                                return r0;
                            };
                            r5 = r5.bind(r6)(r3);
                            r3 = {};
                            r3['files'] = r5;
                            r5 = r4.playingFileIndex;
                            r3['currentFileIndex'] = r5;
                            r5 = r4.isPlaying;
                            r3['isPlaying'] = r5;
                            r5 = r4.model;
                            r3['model'] = r5;
                            r2 = r3;
                            r3 = r4.onUpdateFileListBlock;
                            if(!r3) { _fun9298_ip = 329; continue _fun9298 }
case 318:
                            r3 = r4.onUpdateFileListBlock;
                            r2 = r3.bind(r4)(r2);
case 329: // try_end0
                            r2 = true;
                            return r2;
case 334:
                            return r1;
case 337: // catch_target0
                            CatchBlockStart(arg_register=1);
                            throw r1;
case 341:
                            return r0;
                        }
                    }
