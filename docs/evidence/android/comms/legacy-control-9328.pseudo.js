function* (a0) { // Original name: ?anon_0_, environment: r0
                        _fun9328: for(var _fun9328_ip = 0; ; ) switch(_fun9328_ip) {
case 0:
                            StartGenerator();
                            r3 = this;
                            ResumeGenerator(result_out_reg=0, return_bool_out_reg=1);
                            if(r1) { _fun9328_ip = 145; continue _fun9328 }
case 12:
                            r2 = a0;
case 15: // try_start_0
                            r4 = r3.send;
                            r1 = r2;
                            r5 = 51;
                            r6 = r5;
                            if(!r1) { _fun9328_ip = 35; continue _fun9328 }
case 32:
                            r6 = 52;
case 35:
                            r1 = [99, 51, 49, 99, 52];
                            r1[5] = r6;
                            r7 = 97;
                            r1[6] = r7;
                            r6 = 98;
                            r1[7] = r6;
                            r6 = 99;
                            r1[8] = r6;
                            r1[9] = r7;
                            r8 = 52;
                            r1[10] = r8;
                            r1[11] = r7;
                            r7 = 56;
                            r1[12] = r7;
                            r1[13] = r6;
                            r6 = 50;
                            r1[14] = r6;
                            r6 = 101;
                            r1[15] = r6;
                            r1[16] = r5;
                            r1 = r4.bind(r3)(r1);
                            SaveGenerator(address=121);
case 119:
                            return r1;
case 121:
                            ResumeGenerator(result_out_reg=1, return_bool_out_reg=4);
                            if(r4) { _fun9328_ip = 138; continue _fun9328 }
case 127:
                            r3['isBleOpen'] = r2;
case 133: // try_end0
                            r2 = true;
                            return r2;
case 138:
                            return r1;
case 141: // catch_target0
                            CatchBlockStart(arg_register=1);
                            throw r1;
case 145:
                            return r0;
                        }
                    }
