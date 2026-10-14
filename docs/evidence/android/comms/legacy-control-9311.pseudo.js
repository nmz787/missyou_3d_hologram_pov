function(a0) { // Original name: bytesToHex, environment: r5
                r2 = a0;
                r1 = r2.map;
                r0 = function(a0) { // Environment: r0
                    r2 = a0;
                    r1 = r2.toString;
                    r0 = 16;
                    r3 = r1.bind(r2)(r0);
                    r2 = r3.padStart;
                    r1 = 2;
                    r0 = '0';
                    r0 = r2.bind(r3)(r1, r0);
                    return r0;
                };
                r2 = r1.bind(r2)(r0);
                r1 = r2.join;
                r0 = ' ';
                r0 = r1.bind(r2)(r0);
                return r0;
            }
