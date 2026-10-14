function* () { // Original name: ?anon_0_, environment: r0
                        _fun9320: for(var _fun9320_ip = 0; ; ) switch(_fun9320_ip) {
case 0:
                            StartGenerator();
                            r3 = this;
                            ResumeGenerator(result_out_reg=0, return_bool_out_reg=1);
                            if(r1) { _fun9320_ip = 55; continue _fun9320 }
case 9: // try_start_0
                            r2 = r3.send;
                            r1 = [99, 51, 49, 99, 52, 53, 97, 98, 99, 97, 52, 97, 56, 99, 50, 101, 51];
                            r1 = r2.bind(r3)(r1);
                            SaveGenerator(address=31);
case 29:
                            return r1;
case 31:
                            ResumeGenerator(result_out_reg=1, return_bool_out_reg=2);
                            if(r2) { _fun9320_ip = 48; continue _fun9320 }
case 37:
                            r2 = true;
                            r3['isOpen'] = r2;
case 45: // try_end0
                            return r2;
case 48:
                            return r1;
case 51: // catch_target0
                            CatchBlockStart(arg_register=1);
                            throw r1;
case 55:
                            return r0;
                        }
                    }
