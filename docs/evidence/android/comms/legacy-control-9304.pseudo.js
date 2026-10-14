function* () { // Original name: ?anon_0_, environment: r0
                        _fun9304: for(var _fun9304_ip = 0; ; ) switch(_fun9304_ip) {
case 0:
                            StartGenerator();
                            r4 = this;
                            ResumeGenerator(result_out_reg=0, return_bool_out_reg=1);
                            if(r1) { _fun9304_ip = 116; continue _fun9304 }
case 9:
                            r2 = undefined;
case 11: // try_start_0
                            r3 = r4.send;
                            r1 = [99, 51, 49, 99, 56, 56, 97, 98, 99, 97, 52, 97, 56, 99, 50, 101, 51];
                            r1 = r3.bind(r4)(r1);
                            SaveGenerator(address=33);
case 31:
                            return r1;
case 33:
                            ResumeGenerator(result_out_reg=1, return_bool_out_reg=3);
                            if(r3) { _fun9304_ip = 109; continue _fun9304 }
case 39:
                            r3 = {};
                            r5 = new Array(0);
                            r3['files'] = r5;
                            r5 = r4.playingFileIndex;
                            r3['currentFileIndex'] = r5;
                            r5 = r4.isPlaying;
                            r3['isPlaying'] = r5;
                            r5 = r4.model;
                            r3['model'] = r5;
                            r2 = r3;
                            r3 = r4.onUpdateFileListBlock;
                            if(!r3) { _fun9304_ip = 104; continue _fun9304 }
case 93:
                            r3 = r4.onUpdateFileListBlock;
                            r2 = r3.bind(r4)(r2);
case 104: // try_end0
                            r2 = true;
                            return r2;
case 109:
                            return r1;
case 112: // catch_target0
                            CatchBlockStart(arg_register=1);
                            throw r1;
case 116:
                            return r0;
                        }
                    }
