function(a0, a1) { // Original name: _parseFileList, environment: r5
                _fun9292: for(var _fun9292_ip = 0; ; ) switch(_fun9292_ip) {
case 0:
                    r12 = a0;
                    r3 = this;
                    r1 = a1;
                    r0 = 6;
                    r11 = r1 - r0;
                    r6 = new Array(0);
                    r17 = r11 - r0;
                    r14 = 9;
                    r10 = 3;
                    r16 = 'gbk';
                    r15 = 4;
                    r2 = 2;
                    r9 = 10;
                    r0 = undefined;
                    r5 = 'utf8';
                    r8 = global;
                    r4 = 13;
                    r7 = r14;
                    if(!(r4 < r17)) { _fun9292_ip = 505; continue _fun9292 }
case 66:
                    r13 = _closure1_slot0;
                    r4 = _closure1_slot1;
                    r4 = r4[r9];
                    r4 = r13.bind(r0)(r4);
                    r19 = r4.Buffer;
                    r18 = r19.from;
                    r4 = r12.slice;
                    r13 = r14 + r2;
                    r4 = r4.bind(r12)(r14, r13);
                    r18 = r18.bind(r19)(r4);
                    r4 = r18.toString;
                    r18 = r4.bind(r18)(r5);
                    r4 = r8.parseInt;
                    r19 = r4.bind(r0)(r18, r9);
                    r4 = r8.isNaN;
                    r20 = r4.bind(r0)(r19);
                    r4 = r14;
                    if(r20) { _fun9292_ip = 452; continue _fun9292 }
case 155:
                    r20 = r19 - r2;
                    r21 = _closure1_slot0;
                    r19 = _closure1_slot1;
                    r19 = r19[r9];
                    r19 = r21.bind(r0)(r19);
                    r22 = r19.Buffer;
                    r21 = r22.from;
                    r23 = r12.slice;
                    r19 = r4 + r15;
                    r19 = r23.bind(r12)(r13, r19);
                    r21 = r21.bind(r22)(r19);
                    r19 = r21.toString;
                    r19 = r19.bind(r21)(r5);
                    r21 = r8.parseInt;
                    r23 = r21.bind(r0)(r19, r9);
                    r21 = r8.isNaN;
                    r21 = r21.bind(r0)(r23);
                    if(r21) { _fun9292_ip = 397; continue _fun9292 }
case 245:
                    r13 = r13 + r2;
                    r20 = r13 + r20;
                    if(!(!(r20 > r17))) { _fun9292_ip = 335; continue _fun9292 }
case 257:
                    r21 = r12.slice;
                    r13 = r13 + r10;
                    r22 = r21.bind(r12)(r13, r20);
                    r13 = _closure1_slot9;
                    r21 = r13.default;
                    r13 = r21.decode;
                    r22 = r13.bind(r21)(r22, r16);
                    r21 = r6.push;
                    r13 = {};
                    r13['index'] = r23;
                    r13['name'] = r22;
                    r13 = r21.bind(r6)(r13);
                    r13 = r20 + r15;
                    r14 = r20;
                    r7 = r14;
                    if(r13 < r17) { _fun9292_ip = 66; continue _fun9292 }
case 330:
                    _fun9292_ip = 505; continue _fun9292;
case 335:
                    r13 = _closure1_slot5;
                    r16 = r13.default;
                    r15 = r16.i;
                    r13 = r8.HermesInternal;
                    r20 = r13.concat;
                    r28 = '⚠️ File name range exceeds buffer end (offset=';
                    r26 = ', end=';
                    r24 = ')';
                    r27 = r4;
                    r25 = r11;
                    r14 = r28[r20](r27, r26, r25, r24, r23);
                    r13 = 'TCPClient';
                    r13 = r15.bind(r16)(r13, r14);
                    r7 = r4;
                    _fun9292_ip = 505; continue _fun9292;
case 397:
                    r13 = _closure1_slot5;
                    r16 = r13.default;
                    r15 = r16.i;
                    r13 = r8.HermesInternal;
                    r17 = r13.concat;
                    r14 = '❌ Invalid index at offset ';
                    r13 = ': ';
                    r14 = r17.bind(r14)(r4, r13, r19);
                    r13 = 'TCPClient';
                    r13 = r15.bind(r16)(r13, r14);
                    r7 = r4;
                    _fun9292_ip = 505; continue _fun9292;
case 452:
                    r13 = _closure1_slot5;
                    r16 = r13.default;
                    r15 = r16.i;
                    r13 = r8.HermesInternal;
                    r17 = r13.concat;
                    r14 = '❌ Invalid file length at offset ';
                    r13 = ': ';
                    r14 = r17.bind(r14)(r4, r13, r18);
                    r13 = 'TCPClient';
                    r13 = r15.bind(r16)(r13, r14);
                    r7 = r4;
case 505:
                    r4 = r12.slice;
                    r7 = r4.bind(r12)(r7, r11);
                    r4 = _closure1_slot0;
                    r1 = _closure1_slot1;
                    r1 = r1[r9];
                    r1 = r4.bind(r0)(r1);
                    r4 = r1.Buffer;
                    r1 = r4.from;
                    r4 = r1.bind(r4)(r7);
                    r1 = r4.toString;
                    r4 = r1.bind(r4)(r5);
                    r1 = r4.trim;
                    r5 = r1.bind(r4)();
                    r4 = r5.match;
                    r1 = /(\d{2})(.{1,2})(1[01])/;
                    r9 = r4.bind(r5)(r1);
                    r1 = 'F1';
                    r5 = 0;
                    r4 = false;
                    if(!r9) { _fun9292_ip = 661; continue _fun9292 }
case 603:
                    r11 = r8.parseInt;
                    r8 = 1;
                    r8 = r9[r8];
                    r8 = r11.bind(r0)(r8);
                    r11 = r3._parseModel;
                    r2 = r9[r2];
                    r2 = r11.bind(r3)(r2);
                    r10 = r9[r10];
                    r9 = '11';
                    r7 = false;
                    if(!(r10 === r9)) { _fun9292_ip = 652; continue _fun9292 }
case 650:
                    r7 = true;
case 652:
                    r4 = r7;
                    r5 = r8;
                    r1 = r2;
case 661:
                    r2 = {};
                    r2['files'] = r6;
                    r2['currentFileIndex'] = r5;
                    r2['isPlaying'] = r4;
                    r2['model'] = r1;
                    r3['fileList'] = r6;
                    r3['playingFileIndex'] = r5;
                    r3['isPlaying'] = r4;
                    r3['model'] = r1;
                    r1 = r3.onUpdateFileListBlock;
                    if(!r1) { _fun9292_ip = 726; continue _fun9292 }
case 715:
                    r1 = r3.onUpdateFileListBlock;
                    r1 = r1.bind(r3)(r2);
case 726:
                    return r0;
                }
            }
