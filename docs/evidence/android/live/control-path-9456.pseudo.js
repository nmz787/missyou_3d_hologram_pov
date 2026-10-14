function(a0, a1) { // Original name: _generateSendBuffer, environment: r5
                _fun9456: for(var _fun9456_ip = 0; ; ) switch(_fun9456_ip) {
case 0:
                    r3 = a0;
                    r7 = typeof r3;
                    r0 = 'string';
                    if(!(r7 !== r0)) { _fun9456_ip = 179; continue _fun9456 }
case 17:
                    r5 = _closure1_slot0;
                    r1 = _closure1_slot1;
                    r4 = 9;
                    r1 = r1[r4];
                    r2 = undefined;
                    r1 = r5.bind(r2)(r1);
                    r5 = r1.Buffer;
                    r1 = r5.isBuffer;
                    r1 = r1.bind(r5)(r3);
                    if(r1) { _fun9456_ip = 177; continue _fun9456 }
case 61:
                    r1 = global;
                    r5 = r1.Uint8Array;
                    r5 = r3 instanceof r5;
                    if(r5) { _fun9456_ip = 143; continue _fun9456 }
case 76:
                    r6 = r1.Array;
                    r5 = r6.isArray;
                    r5 = r5.bind(r6)(r3);
                    if(r5) { _fun9456_ip = 143; continue _fun9456 }
case 95:
                    r6 = r1.TypeError;
                    r1 = r1.HermesInternal;
                    r5 = r1.concat;
                    r1 = 'Invalid data, chunk must be a string or buffer, not ';
                    r9 = r5.bind(r1)(r7);
                    r5 = r6.prototype;
                    r5 = Object.create(r5, {constructor: {value: r6}});
                    r10 = r5;
                    r1 = new r10[r6](r9, r8);
                    r1 = r1 instanceof Object ? r1 : r5;
                    throw r1;
case 143:
                    r1 = _closure1_slot0;
                    r0 = _closure1_slot1;
                    r0 = r0[r4];
                    r0 = r1.bind(r2)(r0);
                    r1 = r0.Buffer;
                    r0 = r1.from;
                    r0 = r0.bind(r1)(r3);
                    return r0;
case 177:
                    return r3;
case 179:
                    r2 = _closure1_slot0;
                    r1 = _closure1_slot1;
                    r0 = 9;
                    r1 = r1[r0];
                    r0 = undefined;
                    r0 = r2.bind(r0)(r1);
                    r2 = r0.Buffer;
                    r1 = r2.from;
                    r0 = a1;
                    r0 = r1.bind(r2)(r3, r0);
                    return r0;
                }
            }
