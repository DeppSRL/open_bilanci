--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

--
-- Data for Name: bilanci_voce; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY bilanci_voce (id, denominazione, descrizione, slug, parent_id, lft, rght, tree_id, level) FROM stdin;
633	funzioni	\N	preventivo-spese-spese-correnti-funzioni	632	4	29	1	3
643	Servizi produttivi	\N	preventivo-spese-spese-correnti-funzioni-servizi-produttivi	633	23	24	1	4
642	Sviluppo economico	\N	preventivo-spese-spese-correnti-funzioni-sviluppo-economico	633	21	22	1	4
641	Turismo	\N	preventivo-spese-spese-correnti-funzioni-turismo	633	19	20	1	4
640	Sport	\N	preventivo-spese-spese-correnti-funzioni-sport	633	17	18	1	4
639	Cultura	\N	preventivo-spese-spese-correnti-funzioni-cultura	633	15	16	1	4
638	Istruzione 	\N	preventivo-spese-spese-correnti-funzioni-istruzione	633	13	14	1	4
637	Viabilità e trasporti	\N	preventivo-spese-spese-correnti-funzioni-viabilita-e-trasporti	633	11	12	1	4
636	Territorio e ambiente	\N	preventivo-spese-spese-correnti-funzioni-territorio-e-ambiente	633	9	10	1	4
635	Sociale	\N	preventivo-spese-spese-correnti-funzioni-sociale	633	7	8	1	4
634	Amministrazione	\N	preventivo-spese-spese-correnti-funzioni-amministrazione	633	5	6	1	4
647	Personale	\N	preventivo-spese-spese-correnti-interventi-personale	646	31	32	1	4
645	Giustizia	\N	preventivo-spese-spese-correnti-funzioni-giustizia	633	27	28	1	4
644	Polizia locale	\N	preventivo-spese-spese-correnti-funzioni-polizia-locale	633	25	26	1	4
658	Istruzione 	\N	preventivo-spese-spese-per-investimenti-funzioni-istruzione	653	53	54	1	4
657	Viabilità e trasporti	\N	preventivo-spese-spese-per-investimenti-funzioni-viabilita-e-trasporti	653	51	52	1	4
656	Territorio e ambiente	\N	preventivo-spese-spese-per-investimenti-funzioni-territorio-e-ambiente	653	49	50	1	4
655	Sociale	\N	preventivo-spese-spese-per-investimenti-funzioni-sociale	653	47	48	1	4
654	Amministrazione	\N	preventivo-spese-spese-per-investimenti-funzioni-amministrazione	653	45	46	1	4
651	Altre spese per interventi correnti	\N	preventivo-spese-spese-correnti-interventi-altre-spese-per-interventi-correnti	646	39	40	1	4
632	Spese correnti	\N	preventivo-spese-spese-correnti	631	3	42	1	2
646	interventi	\N	preventivo-spese-spese-correnti-interventi	632	30	41	1	3
650	Interessi passivi e oneri finanziari diversi	\N	preventivo-spese-spese-correnti-interventi-interessi-passivi-e-oneri-finanziari-diversi	646	37	38	1	4
649	Trasferimenti	\N	preventivo-spese-spese-correnti-interventi-trasferimenti	646	35	36	1	4
648	Prestazioni di servizi	\N	preventivo-spese-spese-correnti-interventi-prestazioni-di-servizi	646	33	34	1	4
662	Sviluppo economico	\N	preventivo-spese-spese-per-investimenti-funzioni-sviluppo-economico	653	61	62	1	4
661	Turismo	\N	preventivo-spese-spese-per-investimenti-funzioni-turismo	653	59	60	1	4
660	Sport	\N	preventivo-spese-spese-per-investimenti-funzioni-sport	653	57	58	1	4
1301	Sociale	\N	preventivo-spese-spese-somma-funzioni-sociale	1299	134	135	1	3
1302	Territorio e ambiente	\N	preventivo-spese-spese-somma-funzioni-territorio-e-ambiente	1299	136	137	1	3
1303	Viabilità e trasporti	\N	preventivo-spese-spese-somma-funzioni-viabilita-e-trasporti	1299	138	139	1	3
1304	Istruzione 	\N	preventivo-spese-spese-somma-funzioni-istruzione	1299	140	141	1	3
1305	Cultura	\N	preventivo-spese-spese-somma-funzioni-cultura	1299	142	143	1	3
1306	Sport	\N	preventivo-spese-spese-somma-funzioni-sport	1299	144	145	1	3
1307	Turismo	\N	preventivo-spese-spese-somma-funzioni-turismo	1299	146	147	1	3
1308	Sviluppo economico	\N	preventivo-spese-spese-somma-funzioni-sviluppo-economico	1299	148	149	1	3
1309	Servizi produttivi	\N	preventivo-spese-spese-somma-funzioni-servizi-produttivi	1299	150	151	1	3
1310	Polizia locale	\N	preventivo-spese-spese-somma-funzioni-polizia-locale	1299	152	153	1	3
603	Imposte (altro)	\N	preventivo-entrate-imposte-e-tasse-imposte-imposte-altro	601	163	164	1	4
601	Imposte	\N	preventivo-entrate-imposte-e-tasse-imposte	600	160	165	1	3
602	Casa e fabbricati	\N	preventivo-entrate-imposte-e-tasse-imposte-casa-e-fabbricati	601	161	162	1	4
1299	_spese_somma_funzioni	\N	preventivo-spese-spese-somma-funzioni	631	131	156	1	2
659	Cultura	\N	preventivo-spese-spese-per-investimenti-funzioni-cultura	653	55	56	1	4
669	Trasferimenti di capitali	\N	preventivo-spese-spese-per-investimenti-interventi-trasferimenti-di-capitale	666	75	76	1	4
671	Acquisizioni di beni mobili	\N	preventivo-spese-spese-per-investimenti-interventi-acquisizioni-di-beni-mobili	666	79	80	1	4
670	Partecipazioni azionarie	\N	preventivo-spese-spese-per-investimenti-interventi-partecipazioni-azionarie	666	77	78	1	4
668	Incarichi professionali esterni	\N	preventivo-spese-spese-per-investimenti-interventi-incarichi-professionali-esterni	666	73	74	1	4
667	Acquisizione di beni immobili	\N	preventivo-spese-spese-per-investimenti-interventi-acquisizione-di-beni-immobili	666	71	72	1	4
665	Giustizia	\N	preventivo-spese-spese-per-investimenti-funzioni-giustizia	653	67	68	1	4
653	funzioni	\N	preventivo-spese-spese-per-investimenti-funzioni	652	44	69	1	3
664	Polizia locale	\N	preventivo-spese-spese-per-investimenti-funzioni-polizia-locale	653	65	66	1	4
663	Servizi produttivi	\N	preventivo-spese-spese-per-investimenti-funzioni-servizi-produttivi	653	63	64	1	4
607	Altri tributi	\N	preventivo-entrate-imposte-e-tasse-altri-tributi	600	172	173	1	3
606	Altre Tasse	\N	preventivo-entrate-imposte-e-tasse-tasse-altre-tasse	604	169	170	1	4
600	Imposte e tasse	\N	preventivo-entrate-imposte-e-tasse	599	159	174	1	2
675	Spese per conto terzi	\N	preventivo-spese-spese-per-conto-terzi	631	103	104	1	2
674	Prestiti	\N	preventivo-spese-prestiti	631	91	102	1	2
604	Tasse	\N	preventivo-entrate-imposte-e-tasse-tasse	600	166	171	1	3
605	Rifiuti	\N	preventivo-entrate-imposte-e-tasse-tasse-rifiuti	604	167	168	1	4
631	SPESE	\N	preventivo-spese	598	2	157	1	1
673	Altri investimenti per interventi	\N	preventivo-spese-spese-per-investimenti-interventi-altri-investimenti-per-interventi	666	85	86	1	4
1051	Prestiti	\N	consuntivo-spese-pagamenti-in-conto-competenza-prestiti	956	612	625	2	3
1117	Parchi	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-territorio-e-ambiente-parchi	1111	753	754	2	6
1119	Viabilità	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-viabilita-e-trasporti-viabilita	1118	757	758	2	6
1390	Avanzo di amministrazione	\N	preventivo-entrate-avanzo-di-amministrazione	599	175	176	1	2
611	Contributi e trasferimenti da altri enti pubblici	\N	preventivo-entrate-contributi-pubblici-contributi-da-altri-enti-pubblici	608	182	183	1	3
610	Contributi e trasferimenti dalla Regione	\N	preventivo-entrate-contributi-pubblici-contributi-dalla-regione	608	180	181	1	3
609	Contributi e trasferimenti dallo Stato	\N	preventivo-entrate-contributi-pubblici-contributi-dallo-stato	608	178	179	1	3
608	Contributi e trasferimenti pubblici	\N	preventivo-entrate-contributi-pubblici	599	177	184	1	2
614	Proventi di beni dell'ente	\N	preventivo-entrate-entrate-extratributarie-proventi-di-beni-dellente	612	188	189	1	3
617	Interessi su anticipazioni o crediti	\N	preventivo-entrate-entrate-extratributarie-interessi-su-anticipazioni-o-crediti	612	190	191	1	3
618	Utili delle aziende partecipate	\N	preventivo-entrate-entrate-extratributarie-utili-delle-aziende-partecipate	612	192	193	1	3
1397	Finanziamenti a breve termine		preventivo-spese-prestiti-finanziamenti-a-breve-termine	674	94	95	1	3
1393	Finanziamenti a breve termine		preventivo-entrate-prestiti-finanziamenti-a-breve-termine	629	218	219	1	3
1396	Anticipazioni di cassa		preventivo-spese-prestiti-anticipazioni-di-cassa	674	92	93	1	3
1395	Assunzioni di mutui e prestiti		preventivo-entrate-prestiti-assunzioni-di-mutui-e-prestiti	629	214	215	1	3
1394	Emissione di prestiti obbligazionari		preventivo-entrate-prestiti-emissione-di-prestiti-obbligazionari	629	216	217	1	3
623	Trasferimenti di capitali dalla Regione	\N	preventivo-entrate-vendite-e-trasferimenti-di-capitali-trasferimenti-di-capitali-dalla-regione	620	202	203	1	3
624	Trasferimenti di capitali da altri enti pubblici	\N	preventivo-entrate-vendite-e-trasferimenti-di-capitali-trasferimenti-di-capitali-da-altri-enti-pubblici	620	204	205	1	3
625	Trasferimenti di capitali da privati	\N	preventivo-entrate-vendite-e-trasferimenti-di-capitali-trasferimenti-di-capitali-da-privati	620	206	207	1	3
620	Vendite e trasferimenti di capitali	\N	preventivo-entrate-vendite-e-trasferimenti-di-capitali	599	197	210	1	2
628	Riscossioni di crediti	\N	preventivo-entrate-vendite-e-trasferimenti-di-capitali-riscossioni-di-crediti	620	208	209	1	3
1300	Amministrazione	\N	preventivo-spese-spese-somma-funzioni-amministrazione	1299	132	133	1	3
1311	Giustizia	\N	preventivo-spese-spese-somma-funzioni-giustizia	1299	154	155	1	3
1392	Anticipazioni di cassa	\N	preventivo-entrate-prestiti-anticipazioni-di-cassa	629	212	213	1	3
598	Preventivo	\N	preventivo	\N	1	224	1	0
630	Entrate per conto terzi	\N	preventivo-entrate-entrate-per-conto-terzi	599	221	222	1	2
599	ENTRATE	\N	preventivo-entrate	598	158	223	1	1
629	Prestiti	\N	preventivo-entrate-prestiti	599	211	220	1	2
1391	Disavanzo di amministrazione	\N	preventivo-spese-disavanzo-di-amministrazione	631	89	90	1	2
1400	Quota capitale di debiti pluriennali		preventivo-spese-prestiti-quota-capitale-di-debiti-pluriennali	674	98	99	1	3
1398	Quota capitale di mutui e prestiti		preventivo-spese-prestiti-quota-capitale-di-mutui-e-prestiti	674	100	101	1	3
613	Servizi pubblici	\N	preventivo-entrate-entrate-extratributarie-servizi-pubblici	612	186	187	1	3
612	Entrate extratributarie	\N	preventivo-entrate-entrate-extratributarie	599	185	196	1	2
619	Altre entrate extratributarie	\N	preventivo-entrate-entrate-extratributarie-altre-entrate-extratributarie	612	194	195	1	3
621	Alienazione del patrimonio	\N	preventivo-entrate-vendite-e-trasferimenti-di-capitali-alienazione-del-patrimonio	620	198	199	1	3
622	Trasferimenti di capitali dallo Stato	\N	preventivo-entrate-vendite-e-trasferimenti-di-capitali-trasferimenti-di-capitali-dallo-stato	620	200	201	1	3
1399	Prestiti obbligazionari	\N	preventivo-spese-prestiti-prestiti-obbligazionari	674	96	97	1	3
652	Spese per investimenti	\N	preventivo-spese-spese-per-investimenti	631	43	88	1	2
666	interventi	\N	preventivo-spese-spese-per-investimenti-interventi	652	70	87	1	3
672	Conferimenti di capitale	\N	preventivo-spese-spese-per-investimenti-interventi-conferimenti-di-capitale	666	83	84	1	4
1401	Concessioni di crediti e anticipazioni	\N	preventivo-spese-spese-per-investimenti-interventi-concessioni-di-crediti-e-anticipazioni	666	81	82	1	4
820	Rifiuti	\N	consuntivo-entrate-cassa-imposte-e-tasse-tasse-rifiuti	819	1510	1511	2	5
1421	Prestiti obbligazionari	\N	consuntivo-spese-cassa-prestiti-prestiti-obbligazionari	1245	1033	1034	2	4
791	Turismo	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-servizi-pubblici-turismo	784	1442	1443	2	5
1190	Giustizia	\N	consuntivo-spese-cassa-spese-correnti-funzioni-giustizia	1152	914	915	2	5
1025	Istruzione	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-istruzione	1004	556	567	2	5
906	Spese per investimenti	\N	consuntivo-spese-impegni-spese-per-investimenti	859	228	325	2	3
952	Conferimenti di capitale	\N	consuntivo-spese-impegni-spese-per-investimenti-interventi-conferimenti-di-capitale	946	320	321	2	5
985	Cultura	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-cultura	958	476	481	2	5
1246	Spese per conto terzi	\N	consuntivo-spese-cassa-spese-per-conto-terzi	1150	1042	1043	2	3
679	Imposte e tasse	\N	consuntivo-entrate-accertamenti-imposte-e-tasse	678	1204	1223	2	3
700	Sport	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-servizi-pubblici-sport	694	1244	1245	2	5
1076	Istruzione	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-istruzione	1055	672	683	2	5
1436	Anticipazioni di cassa	\N	consuntivo-spese-pagamenti-in-conto-residui-prestiti-anticipazioni-di-cassa	1148	821	822	2	4
1216	Viabilità	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-viabilita-e-trasporti-viabilita	1215	965	966	2	6
709	Interessi su anticipazioni o crediti	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-interessi-su-anticipazioni-o-crediti	693	1263	1264	2	4
684	Tasse	\N	consuntivo-entrate-accertamenti-imposte-e-tasse-tasse	679	1215	1222	2	4
1333	Istruzione	\N	consuntivo-spese-cassa-spese-somma-funzioni-istruzione	1312	1163	1174	2	4
1154	Organi istituzionali	\N	consuntivo-spese-cassa-spese-correnti-funzioni-amministrazione-organi-istituzionali	1153	841	842	2	6
815	Imposte	\N	consuntivo-entrate-cassa-imposte-e-tasse-imposte	814	1501	1508	2	4
1179	Cultura	\N	consuntivo-spese-cassa-spese-correnti-funzioni-cultura	1152	892	897	2	5
856	Prestiti	\N	consuntivo-entrate-cassa-prestiti	813	1564	1573	2	3
813	Cassa	\N	consuntivo-entrate-cassa	677	1497	1594	2	2
680	Imposte	\N	consuntivo-entrate-accertamenti-imposte-e-tasse-imposte	679	1207	1214	2	4
1341	Teatri	\N	consuntivo-spese-cassa-spese-somma-funzioni-cultura-teatri	1339	1178	1179	2	5
1191	interventi	\N	consuntivo-spese-cassa-spese-correnti-interventi	1151	917	928	2	4
1196	Altre spese per interventi correnti	\N	consuntivo-spese-cassa-spese-correnti-interventi-altre-spese-per-interventi-correnti	1191	926	927	2	5
1351	_spese_somma_funzioni	\N	consuntivo-spese-impegni-spese-somma-funzioni	859	342	419	2	3
774	Tasse	\N	consuntivo-entrate-riscossioni-in-conto-residui-imposte-e-tasse-tasse	769	1411	1418	2	4
777	Altre Tasse	\N	consuntivo-entrate-riscossioni-in-conto-residui-imposte-e-tasse-tasse-altre-tasse	774	1416	1417	2	5
900	interventi	\N	consuntivo-spese-impegni-spese-correnti-interventi	860	215	226	2	4
1186	Turismo	\N	consuntivo-spese-cassa-spese-correnti-funzioni-turismo	1152	906	907	2	5
1228	Sport	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-sport	1198	990	997	2	5
1050	Altri investimenti per interventi	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-interventi-altri-investimenti-per-interventi	1043	608	609	2	5
868	Residenze per anziani	\N	consuntivo-spese-impegni-spese-correnti-funzioni-sociale-residenze-per-anziani	865	149	150	2	6
869	Assistenza, beneficenza e altro	\N	consuntivo-spese-impegni-spese-correnti-funzioni-sociale-assistenza-beneficenza-e-altro	865	151	152	2	6
987	Teatri	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-cultura-teatri	985	479	480	2	6
1481	Per Spese in Conto Capitale		consuntivo-riassuntivo-risultato-di-amministrazione-per-spese-in-conto-capitale	1478	110	111	2	3
1478	Risultato di amministrazione	\N	consuntivo-riassuntivo-risultato-di-amministrazione	1446	105	116	2	2
1480	Vincolato	\N	consuntivo-riassuntivo-risultato-di-amministrazione-vincolato	1478	114	115	2	3
1482	Per fondo ammortamento	\N	consuntivo-riassuntivo-risultato-di-amministrazione-per-fondo-ammortamento	1478	108	109	2	3
1483	Non vincolato	\N	consuntivo-riassuntivo-risultato-di-amministrazione-non-vincolato	1478	106	107	2	3
1021	Viabilità e trasporti	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-viabilita-e-trasporti	1004	548	555	2	5
678	Accertamenti	\N	consuntivo-entrate-accertamenti	677	1203	1300	2	2
1458	Residui passivi	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-residui-residui-passivi	1448	53	54	2	4
1462	Pagamenti	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-competenza-pagamenti	1449	27	28	2	4
1463	Fondo di cassa al 31 dicembre	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-competenza-fondo-di-cassa-al-31-dicembre	1449	25	26	2	4
965	Residenze per anziani	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-sociale-residenze-per-anziani	962	435	436	2	6
1024	Illuminazione pubblica	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-viabilita-e-trasporti-illuminazione-pubblica	1021	553	554	2	6
701	Turismo	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-servizi-pubblici-turismo	694	1246	1247	2	5
895	Turismo	\N	consuntivo-spese-impegni-spese-correnti-funzioni-turismo	861	204	205	2	5
867	Prevenzione e riabilitazione	\N	consuntivo-spese-impegni-spese-correnti-funzioni-sociale-prevenzione-e-riabilitazione	865	147	148	2	6
855	Riscossioni di crediti	\N	consuntivo-entrate-cassa-vendite-e-trasferimenti-di-capitali-riscossioni-di-crediti	847	1591	1592	2	4
812	Entrate per conto terzi	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-per-conto-terzi	768	1476	1477	2	3
1313	Amministrazione	\N	consuntivo-spese-cassa-spese-somma-funzioni-amministrazione	1312	1123	1128	2	4
1402	Anticipazioni di cassa	\N	consuntivo-entrate-accertamenti-prestiti-anticipazioni-di-cassa	721	1271	1272	2	4
1315	Amministrazione (altro)	\N	consuntivo-spese-cassa-spese-somma-funzioni-amministrazione-amministrazione-altro	1313	1126	1127	2	5
1040	Servizi produttivi	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-servizi-produttivi	1004	586	587	2	5
767	Entrate per conto terzi	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-per-conto-terzi	723	1378	1379	2	3
1151	Spese correnti	\N	consuntivo-spese-cassa-spese-correnti	1150	838	929	2	3
1451	Fondo di cassa al 1° gennaio	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-residui-fondo-di-cassa-al-1°-gennaio	1448	43	44	2	4
1192	Personale	\N	consuntivo-spese-cassa-spese-correnti-interventi-personale	1191	918	919	2	5
954	Prestiti	\N	consuntivo-spese-impegni-prestiti	859	326	339	2	3
1446	RIASSUNTIVO	\N	consuntivo-riassuntivo	676	2	133	2	1
1185	Manifestazioni sportive	\N	consuntivo-spese-cassa-spese-correnti-funzioni-sport-manifestazioni-sportive	1182	903	904	2	6
840	Altri servizi	\N	consuntivo-entrate-cassa-entrate-extratributarie-servizi-pubblici-altri-servizi	829	1548	1549	2	5
763	Permessi di costruire  e sanzioni	\N	consuntivo-entrate-riscossioni-in-conto-competenza-vendite-e-trasferimenti-di-capitali-trasferimenti-di-capitali-da-privati-permessi-di-costruire-e-sanzioni	762	1390	1391	2	5
782	Contributi e trasferimenti da altri enti pubblici	\N	consuntivo-entrate-riscossioni-in-conto-residui-contributi-pubblici-contributi-da-altri-enti-pubblici	779	1425	1426	2	4
705	Altri servizi	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-servizi-pubblici-altri-servizi	694	1254	1255	2	5
907	funzioni	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni	906	229	306	2	4
677	ENTRATE	\N	consuntivo-entrate	676	1202	1595	2	1
1317	Asili nido	\N	consuntivo-spese-cassa-spese-somma-funzioni-sociale-asili-nido	1316	1130	1131	2	5
957	Spese correnti	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti	956	422	513	2	3
1346	Turismo	\N	consuntivo-spese-cassa-spese-somma-funzioni-turismo	1312	1189	1190	2	4
1434	Quota capitale di debiti pluriennali	\N	consuntivo-spese-pagamenti-in-conto-competenza-prestiti-quota-capitale-di-debiti-pluriennali	1051	619	620	2	4
720	Riscossioni di crediti	\N	consuntivo-entrate-accertamenti-vendite-e-trasferimenti-di-capitali-riscossioni-di-crediti	712	1297	1298	2	4
728	Imposte (altro)	\N	consuntivo-entrate-riscossioni-in-conto-competenza-imposte-e-tasse-imposte-imposte-altro	725	1310	1311	2	5
801	Altre entrate extratributarie	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-altre-entrate-extratributarie	783	1463	1464	2	4
1319	Residenze per anziani	\N	consuntivo-spese-cassa-spese-somma-funzioni-sociale-residenze-per-anziani	1316	1134	1135	2	5
1046	Trasferimenti di capitale	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-interventi-trasferimenti-di-capitale	1043	598	599	2	5
1312	_spese_somma_funzioni	\N	consuntivo-spese-cassa-spese-somma-funzioni	1150	1122	1199	2	3
1378	Cultura	\N	consuntivo-spese-impegni-spese-somma-funzioni-cultura	1351	395	400	2	4
1238	Acquisizione di beni immobili	\N	consuntivo-spese-cassa-spese-per-investimenti-interventi-acquisizione-di-beni-immobili	1237	1010	1011	2	5
1241	Partecipazioni azionarie	\N	consuntivo-spese-cassa-spese-per-investimenti-interventi-partecipazioni-azionarie	1237	1016	1017	2	5
1357	Prevenzione e riabilitazione	\N	consuntivo-spese-impegni-spese-somma-funzioni-sociale-prevenzione-e-riabilitazione	1355	352	353	2	5
1358	Residenze per anziani	\N	consuntivo-spese-impegni-spese-somma-funzioni-sociale-residenze-per-anziani	1355	354	355	2	5
1349	Polizia locale	\N	consuntivo-spese-cassa-spese-somma-funzioni-polizia-locale	1312	1195	1196	2	4
943	Servizi produttivi	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-servizi-produttivi	907	300	301	2	5
865	Sociale	\N	consuntivo-spese-impegni-spese-correnti-funzioni-sociale	861	144	155	2	5
1042	Giustizia	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-giustizia	1004	590	591	2	5
716	Trasferimenti da altri enti pubblici	\N	consuntivo-entrate-accertamenti-vendite-e-trasferimenti-di-capitali-trasferimenti-da-altri-enti-pubblici	712	1289	1290	2	4
753	Altri proventi	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-proventi-di-beni-dellente-altri-proventi	751	1358	1359	2	5
1222	Istruzione media	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-istruzione-istruzione-media	1219	977	978	2	6
1226	Biblioteche e musei	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-cultura-biblioteche-e-musei	1225	985	986	2	6
1225	Cultura	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-cultura	1198	984	989	2	5
933	Assistenza, trasporto, mense	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-istruzione-assistenza-trasporto-mense	928	279	280	2	6
766	Prestiti	\N	consuntivo-entrate-riscossioni-in-conto-competenza-prestiti	723	1368	1377	2	3
1199	Amministrazione	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-amministrazione	1198	932	937	2	5
958	funzioni	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni	957	423	500	2	4
768	Riscossioni in conto residui	\N	consuntivo-entrate-riscossioni-in-conto-residui	677	1399	1496	2	2
1217	Trasporti pubblici	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-viabilita-e-trasporti-trasporti-pubblici	1215	967	968	2	6
1145	Acquisizioni di beni mobili	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-interventi-acquisizioni-di-beni-mobili	1140	810	811	2	5
861	funzioni	\N	consuntivo-spese-impegni-spese-correnti-funzioni	860	137	214	2	4
898	Polizia locale	\N	consuntivo-spese-impegni-spese-correnti-funzioni-polizia-locale	861	210	211	2	5
1198	funzioni	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni	1197	931	1008	2	4
1215	Viabilità e trasporti	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-viabilita-e-trasporti	1198	964	971	2	5
1364	Protezione civile	\N	consuntivo-spese-impegni-spese-somma-funzioni-territorio-e-ambiente-protezione-civile	1361	366	367	2	5
1365	Servizio idrico	\N	consuntivo-spese-impegni-spese-somma-funzioni-territorio-e-ambiente-servizio-idrico	1361	368	369	2	5
995	Polizia locale	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-polizia-locale	958	496	497	2	5
1439	Prestiti obbligazionari	\N	consuntivo-spese-pagamenti-in-conto-residui-prestiti-prestiti-obbligazionari	1148	825	826	2	4
1211	Protezione civile	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-territorio-e-ambiente-protezione-civile	1208	955	956	2	6
1212	Servizio idrico	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-territorio-e-ambiente-servizio-idrico	1208	957	958	2	6
814	Imposte e tasse	\N	consuntivo-entrate-cassa-imposte-e-tasse	813	1498	1517	2	3
1412	Assunzioni di mutui e prestiti	\N	consuntivo-entrate-riscossioni-in-conto-residui-prestiti-assunzioni-di-mutui-e-prestiti	811	1469	1470	2	4
1240	Trasferimenti di capitale	\N	consuntivo-spese-cassa-spese-per-investimenti-interventi-trasferimenti-di-capitale	1237	1014	1015	2	5
1163	Urbanistica e territorio	\N	consuntivo-spese-cassa-spese-correnti-funzioni-territorio-e-ambiente-urbanistica-e-territorio	1162	859	860	2	6
1336	Istruzione media	\N	consuntivo-spese-cassa-spese-somma-funzioni-istruzione-istruzione-media	1333	1168	1169	2	5
835	Sport	\N	consuntivo-entrate-cassa-entrate-extratributarie-servizi-pubblici-sport	829	1538	1539	2	5
1054	Spese correnti	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti	1053	630	721	2	3
1020	Parchi	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-territorio-e-ambiente-parchi	1014	545	546	2	6
1022	Viabilità	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-viabilita-e-trasporti-viabilita	1021	549	550	2	6
1023	Trasporti pubblici	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-viabilita-e-trasporti-trasporti-pubblici	1021	551	552	2	6
1327	Rifiuti	\N	consuntivo-spese-cassa-spese-somma-funzioni-territorio-e-ambiente-rifiuti	1322	1150	1151	2	5
870	Cimiteri	\N	consuntivo-spese-impegni-spese-correnti-funzioni-sociale-cimiteri	865	153	154	2	6
689	Contributi e trasferimenti pubblici	\N	consuntivo-entrate-accertamenti-contributi-pubblici	678	1224	1231	2	3
1438	Quota capitale di mutui e prestiti	\N	consuntivo-spese-pagamenti-in-conto-residui-prestiti-quota-capitale-di-mutui-e-prestiti	1148	829	830	2	4
1440	Quota capitale di debiti pluriennali	\N	consuntivo-spese-pagamenti-in-conto-residui-prestiti-quota-capitale-di-debiti-pluriennali	1148	827	828	2	4
1326	Servizio idrico	\N	consuntivo-spese-cassa-spese-somma-funzioni-territorio-e-ambiente-servizio-idrico	1322	1148	1149	2	5
1442	Concessioni di crediti e anticipazioni	\N	consuntivo-spese-impegni-spese-per-investimenti-interventi-concessioni-di-crediti-e-anticipazioni	946	318	319	2	5
816	Casa e fabbricati	\N	consuntivo-entrate-cassa-imposte-e-tasse-imposte-casa-e-fabbricati	815	1502	1503	2	5
946	interventi	\N	consuntivo-spese-impegni-spese-per-investimenti-interventi	906	307	324	2	4
953	Altri investimenti per interventi	\N	consuntivo-spese-impegni-spese-per-investimenti-interventi-altri-investimenti-per-interventi	946	322	323	2	5
1485	Reinvestimento quote accantonate per ammortamento	\N	consuntivo-riassuntivo-utilizzo-avanzo-di-amministrazione-esercizio-precedente-reinvestimento-quote-accantonate-per-ammortamento	1484	122	123	2	3
1486	Finanziamento debiti fuori bilancio	\N	consuntivo-riassuntivo-utilizzo-avanzo-di-amministrazione-esercizio-precedente-finanziamento-debiti-fuori-bilancio	1484	120	121	2	3
1389	Giustizia	\N	consuntivo-spese-impegni-spese-somma-funzioni-giustizia	1351	417	418	2	4
1427	Prestiti obbligazionari	\N	consuntivo-spese-impegni-prestiti-prestiti-obbligazionari	954	331	332	2	4
1426	Quota capitale di mutui e prestiti	\N	consuntivo-spese-impegni-prestiti-quota-capitale-di-mutui-e-prestiti	954	335	336	2	4
1181	Teatri	\N	consuntivo-spese-cassa-spese-correnti-funzioni-cultura-teatri	1179	895	896	2	6
1487	Salvaguardia equilibri di bilancio	\N	consuntivo-riassuntivo-utilizzo-avanzo-di-amministrazione-esercizio-precedente-salvaguardia-equilibri-di-bilancio	1484	124	125	2	3
1110	Cimiteri	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-sociale-cimiteri	1105	739	740	2	6
1039	Sviluppo economico	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-sviluppo-economico	1004	584	585	2	5
843	Altri proventi	\N	consuntivo-entrate-cassa-entrate-extratributarie-proventi-di-beni-dellente-altri-proventi	841	1554	1555	2	5
735	Contributi e trasferimenti dallo Stato	\N	consuntivo-entrate-riscossioni-in-conto-competenza-contributi-pubblici-contributi-dallo-stato	734	1323	1324	2	4
723	Riscossioni in conto competenza	\N	consuntivo-entrate-riscossioni-in-conto-competenza	677	1301	1398	2	2
879	Viabilità	\N	consuntivo-spese-impegni-spese-correnti-funzioni-viabilita-e-trasporti-viabilita	878	171	172	2	6
904	Interessi passivi e oneri finanziari diversi	\N	consuntivo-spese-impegni-spese-correnti-interventi-interessi-passivi-e-oneri-finanziari-diversi	900	222	223	2	5
1356	Asili nido	\N	consuntivo-spese-impegni-spese-somma-funzioni-sociale-asili-nido	1355	350	351	2	5
935	Biblioteche e musei	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-cultura-biblioteche-e-musei	934	283	284	2	6
1340	Biblioteche e musei	\N	consuntivo-spese-cassa-spese-somma-funzioni-cultura-biblioteche-e-musei	1339	1176	1177	2	5
1200	Organi istituzionali	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-amministrazione-organi-istituzionali	1199	933	934	2	6
1355	Sociale	\N	consuntivo-spese-impegni-spese-somma-funzioni-sociale	1351	349	360	2	4
1321	Cimiteri	\N	consuntivo-spese-cassa-spese-somma-funzioni-sociale-cimiteri	1316	1138	1139	2	5
699	Cultura	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-servizi-pubblici-cultura	694	1242	1243	2	5
921	Servizio idrico	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-territorio-e-ambiente-servizio-idrico	917	255	256	2	6
922	Rifiuti	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-territorio-e-ambiente-rifiuti	917	257	258	2	6
1380	Teatri	\N	consuntivo-spese-impegni-spese-somma-funzioni-cultura-teatri	1378	398	399	2	5
1235	Polizia locale	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-polizia-locale	1198	1004	1005	2	5
1236	Giustizia	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-giustizia	1198	1006	1007	2	5
1239	Incarichi professionali esterni	\N	consuntivo-spese-cassa-spese-per-investimenti-interventi-incarichi-professionali-esterni	1237	1012	1013	2	5
1106	Asili nido	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-sociale-asili-nido	1105	731	732	2	6
891	Sport	\N	consuntivo-spese-impegni-spese-correnti-funzioni-sport	861	196	203	2	5
903	Trasferimenti	\N	consuntivo-spese-impegni-spese-correnti-interventi-trasferimenti	900	220	221	2	5
926	Trasporti pubblici	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-viabilita-e-trasporti-trasporti-pubblici	924	265	266	2	6
1183	Piscine comunali	\N	consuntivo-spese-cassa-spese-correnti-funzioni-sport-piscine-comunali	1182	899	900	2	6
1374	Istruzione elementare	\N	consuntivo-spese-impegni-spese-somma-funzioni-istruzione-istruzione-elementare	1372	386	387	2	5
1187	Sviluppo economico	\N	consuntivo-spese-cassa-spese-correnti-funzioni-sviluppo-economico	1152	908	909	2	5
1381	Sport	\N	consuntivo-spese-impegni-spese-somma-funzioni-sport	1351	401	408	2	4
828	Entrate extratributarie	\N	consuntivo-entrate-cassa-entrate-extratributarie	813	1526	1563	2	3
811	Prestiti	\N	consuntivo-entrate-riscossioni-in-conto-residui-prestiti	768	1466	1475	2	3
848	Alienazione del patrimonio	\N	consuntivo-entrate-cassa-vendite-e-trasferimenti-di-capitali-alienazione-del-patrimonio	847	1577	1578	2	4
1245	Prestiti	\N	consuntivo-spese-cassa-prestiti	1150	1028	1041	2	3
916	Cimiteri	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-sociale-cimiteri	911	245	246	2	6
866	Asili nido	\N	consuntivo-spese-impegni-spese-correnti-funzioni-sociale-asili-nido	865	145	146	2	6
894	Manifestazioni sportive	\N	consuntivo-spese-impegni-spese-correnti-funzioni-sport-manifestazioni-sportive	891	201	202	2	6
874	Protezione civile	\N	consuntivo-spese-impegni-spese-correnti-funzioni-territorio-e-ambiente-protezione-civile	871	161	162	2	6
899	Giustizia	\N	consuntivo-spese-impegni-spese-correnti-funzioni-giustizia	861	212	213	2	5
1331	Trasporti pubblici	\N	consuntivo-spese-cassa-spese-somma-funzioni-viabilita-e-trasporti-trasporti-pubblici	1329	1158	1159	2	5
873	Edilizia pubblica	\N	consuntivo-spese-impegni-spese-correnti-funzioni-territorio-e-ambiente-edilizia-pubblica	871	159	160	2	6
1202	Sociale	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-sociale	1198	938	949	2	5
956	Pagamenti in conto competenza	\N	consuntivo-spese-pagamenti-in-conto-competenza	858	421	628	2	2
1330	Viabilità	\N	consuntivo-spese-cassa-spese-somma-funzioni-viabilita-e-trasporti-viabilita	1329	1156	1157	2	5
1329	Viabilità e trasporti	\N	consuntivo-spese-cassa-spese-somma-funzioni-viabilita-e-trasporti	1312	1155	1162	2	4
875	Servizio idrico	\N	consuntivo-spese-impegni-spese-correnti-funzioni-territorio-e-ambiente-servizio-idrico	871	163	164	2	6
1419	Finanziamenti a breve termine	\N	consuntivo-spese-cassa-prestiti-finanziamenti-a-breve-termine	1245	1031	1032	2	4
1350	Giustizia	\N	consuntivo-spese-cassa-spese-somma-funzioni-giustizia	1312	1197	1198	2	4
1068	Protezione civile	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-territorio-e-ambiente-protezione-civile	1065	655	656	2	6
1069	Servizio idrico	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-territorio-e-ambiente-servizio-idrico	1065	657	658	2	6
1070	Rifiuti	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-territorio-e-ambiente-rifiuti	1065	659	660	2	6
1065	Territorio e ambiente	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-territorio-e-ambiente	1055	650	663	2	5
1043	interventi	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-interventi	1003	593	610	2	4
966	Assistenza, beneficenza e altro	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-sociale-assistenza-beneficenza-e-altro	962	437	438	2	6
760	Trasferimenti dalla Regione	\N	consuntivo-entrate-riscossioni-in-conto-competenza-vendite-e-trasferimenti-di-capitali-trasferimenti-dalla-regione	757	1385	1386	2	4
839	Sociale	\N	consuntivo-entrate-cassa-entrate-extratributarie-servizi-pubblici-sociale	829	1546	1547	2	5
775	Rifiuti	\N	consuntivo-entrate-riscossioni-in-conto-residui-imposte-e-tasse-tasse-rifiuti	774	1412	1413	2	5
1232	Turismo	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-turismo	1198	998	999	2	5
1334	Scuola materna	\N	consuntivo-spese-cassa-spese-somma-funzioni-istruzione-scuola-materna	1333	1164	1165	2	5
1037	Manifestazioni sportive	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-sport-manifestazioni-sportive	1034	579	580	2	6
1038	Turismo	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-turismo	1004	582	583	2	5
882	Istruzione	\N	consuntivo-spese-impegni-spese-correnti-funzioni-istruzione	861	178	189	2	5
909	Organi istituzionali	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-amministrazione-organi-istituzionali	908	231	232	2	6
1003	Spese per investimenti	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti	956	514	611	2	3
1425	Finanziamenti a breve termine	\N	consuntivo-spese-impegni-prestiti-finanziamenti-a-breve-termine	954	329	330	2	4
736	Contributi e trasferimenti dalla Regione	\N	consuntivo-entrate-riscossioni-in-conto-competenza-contributi-pubblici-contributi-dalla-regione	734	1325	1326	2	4
730	Rifiuti	\N	consuntivo-entrate-riscossioni-in-conto-competenza-imposte-e-tasse-tasse-rifiuti	729	1314	1315	2	5
942	Sviluppo economico	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-sviluppo-economico	907	298	299	2	5
1339	Cultura	\N	consuntivo-spese-cassa-spese-somma-funzioni-cultura	1312	1175	1180	2	4
886	Istruzione secondaria superiore	\N	consuntivo-spese-impegni-spese-correnti-funzioni-istruzione-istruzione-secondaria-superiore	882	185	186	2	6
727	Addizionale IRPEF	\N	consuntivo-entrate-riscossioni-in-conto-competenza-imposte-e-tasse-imposte-addizionale-irpef	725	1308	1309	2	5
749	Sociale	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-servizi-pubblici-sociale	739	1350	1351	2	5
1036	Stadio e altri impianti	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-sport-stadio-e-altri-impianti	1034	577	578	2	6
1034	Sport	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-sport	1004	574	581	2	5
878	Viabilità e trasporti	\N	consuntivo-spese-impegni-spese-correnti-funzioni-viabilita-e-trasporti	861	170	177	2	5
721	Prestiti	\N	consuntivo-entrate-accertamenti-prestiti	678	1270	1279	2	3
928	Istruzione	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-istruzione	907	270	281	2	5
1085	Sport	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-sport	1055	690	697	2	5
1156	Sociale	\N	consuntivo-spese-cassa-spese-correnti-funzioni-sociale	1152	846	857	2	5
1430	Anticipazioni di cassa	\N	consuntivo-spese-pagamenti-in-conto-competenza-prestiti-anticipazioni-di-cassa	1051	613	614	2	4
819	Tasse	\N	consuntivo-entrate-cassa-imposte-e-tasse-tasse	814	1509	1516	2	4
823	Altri tributi		consuntivo-entrate-cassa-imposte-e-tasse-tributi-speciali	814	1499	1500	2	4
818	Imposte (altro)	\N	consuntivo-entrate-cassa-imposte-e-tasse-imposte-imposte-altro	815	1506	1507	2	5
1314	Organi istituzionali	\N	consuntivo-spese-cassa-spese-somma-funzioni-amministrazione-organi-istituzionali	1313	1124	1125	2	5
1316	Sociale	\N	consuntivo-spese-cassa-spese-somma-funzioni-sociale	1312	1129	1140	2	4
1153	Amministrazione	\N	consuntivo-spese-cassa-spese-correnti-funzioni-amministrazione	1152	840	845	2	5
1501	Eventuale disavanzo da riaccertamento dei residui	\N	consuntivo-riassuntivo-riaccertamento-dei-residui-eventuale-disavanzo-da-riaccertamento-dei-residui	1500	98	99	2	3
1129	Biblioteche e musei	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-cultura-biblioteche-e-musei	1128	777	778	2	6
919	Edilizia pubblica	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-territorio-e-ambiente-edilizia-pubblica	917	251	252	2	6
842	Canone Occupazione Spazi e Aree Pubbliche	\N	consuntivo-entrate-cassa-entrate-extratributarie-proventi-di-beni-dellente-canone-occupazione-spazi-e-aree-pubbliche	841	1552	1553	2	5
887	Assistenza, trasporto, mense	\N	consuntivo-spese-impegni-spese-correnti-funzioni-istruzione-assistenza-trasporto-mense	882	187	188	2	6
889	Biblioteche e musei	\N	consuntivo-spese-impegni-spese-correnti-funzioni-cultura-biblioteche-e-musei	888	191	192	2	6
888	Cultura	\N	consuntivo-spese-impegni-spese-correnti-funzioni-cultura	861	190	195	2	5
890	Teatri	\N	consuntivo-spese-impegni-spese-correnti-funzioni-cultura-teatri	888	193	194	2	6
1229	Piscine comunali	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-sport-piscine-comunali	1228	991	992	2	6
955	Spese per conto terzi	\N	consuntivo-spese-impegni-spese-per-conto-terzi	859	340	341	2	3
1041	Polizia locale	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-polizia-locale	1004	588	589	2	5
1488	Spese correnti non ripetitive	\N	consuntivo-riassuntivo-utilizzo-avanzo-di-amministrazione-esercizio-precedente-spese-correnti-non-ripetitive	1484	128	129	2	3
1489	Spese correnti in sede di assestamento	\N	consuntivo-riassuntivo-utilizzo-avanzo-di-amministrazione-esercizio-precedente-spese-correnti-in-sede-di-assestamento	1484	126	127	2	3
1105	Sociale	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-sociale	1101	730	741	2	5
860	Spese correnti	\N	consuntivo-spese-impegni-spese-correnti	859	136	227	2	3
934	Cultura	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-cultura	907	282	287	2	5
1122	Istruzione	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-istruzione	1101	764	775	2	5
1127	Assistenza, trasporto, mense	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-istruzione-assistenza-trasporto-mense	1122	773	774	2	6
747	Viabilità e trasporti	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-servizi-pubblici-viabilita-e-trasporti	739	1346	1347	2	5
832	Polizia locale	\N	consuntivo-entrate-cassa-entrate-extratributarie-servizi-pubblici-polizia-locale	829	1532	1533	2	5
1372	Istruzione	\N	consuntivo-spese-impegni-spese-somma-funzioni-istruzione	1351	383	394	2	4
1237	interventi	\N	consuntivo-spese-cassa-spese-per-investimenti-interventi	1197	1009	1026	2	4
1342	Sport	\N	consuntivo-spese-cassa-spese-somma-funzioni-sport	1312	1181	1188	2	4
1152	funzioni	\N	consuntivo-spese-cassa-spese-correnti-funzioni	1151	839	916	2	4
1467	Residui passivi	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-competenza-residui-passivi	1449	33	34	2	4
1449	Gestione competenza	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-competenza	1447	20	39	2	3
1448	Gestione residui	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-residui	1447	40	59	2	3
714	Trasferimenti dallo Stato	\N	consuntivo-entrate-accertamenti-vendite-e-trasferimenti-di-capitali-trasferimenti-dallo-stato	712	1285	1286	2	4
1149	Spese per conto terzi	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-conto-terzi	1053	834	835	2	3
877	Parchi	\N	consuntivo-spese-impegni-spese-correnti-funzioni-territorio-e-ambiente-parchi	871	167	168	2	6
902	Prestazioni di servizi	\N	consuntivo-spese-impegni-spese-correnti-interventi-prestazioni-di-servizi	900	218	219	2	5
1464	Pagamenti per azioni esecutive non regolarizzate al 31.12	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-competenza-pagamenti-per-azioni-esecutive-non-regolarizzate-al-31.12	1449	29	30	2	4
1465	Differenza	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-competenza-differenza	1449	21	22	2	4
1452	Riscossioni	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-residui-riscossioni	1448	55	56	2	4
734	Contributi e trasferimenti pubblici	\N	consuntivo-entrate-riscossioni-in-conto-competenza-contributi-pubblici	723	1322	1329	2	3
779	Contributi e trasferimenti pubblici	\N	consuntivo-entrate-riscossioni-in-conto-residui-contributi-pubblici	768	1420	1427	2	3
824	Contributi e trasferimenti pubblici	\N	consuntivo-entrate-cassa-contributi-pubblici	813	1518	1525	2	3
826	Contributi e trasferimenti dalla Regione	\N	consuntivo-entrate-cassa-contributi-pubblici-contributi-dalla-regione	824	1521	1522	2	4
1475	Residui attivi	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-totale-residui-attivi	1450	71	72	2	4
1506	Copertura di disavanzi di consorzi, aziende speciali e di istituzioni	\N	consuntivo-riassuntivo-debiti-fuori-bilancio-copertura-di-disavanzi-di-consorzi-aziende-speciali-e-di-istituzioni	1504	6	7	2	3
1171	Trasporti pubblici	\N	consuntivo-spese-cassa-spese-correnti-funzioni-viabilita-e-trasporti-trasporti-pubblici	1169	875	876	2	6
1169	Viabilità e trasporti	\N	consuntivo-spese-cassa-spese-correnti-funzioni-viabilita-e-trasporti	1152	872	879	2	5
1416	Assunzioni di mutui e prestiti	\N	consuntivo-entrate-cassa-prestiti-assunzioni-di-mutui-e-prestiti	856	1567	1568	2	4
1433	Prestiti obbligazionari	\N	consuntivo-spese-pagamenti-in-conto-competenza-prestiti-prestiti-obbligazionari	1051	617	618	2	4
1167	Rifiuti	\N	consuntivo-spese-cassa-spese-correnti-funzioni-territorio-e-ambiente-rifiuti	1162	867	868	2	6
691	Contributi e trasferimenti dalla Regione	\N	consuntivo-entrate-accertamenti-contributi-pubblici-contributi-dalla-regione	689	1227	1228	2	4
858	SPESE	\N	consuntivo-spese	676	134	1201	2	1
1203	Asili nido	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-sociale-asili-nido	1202	939	940	2	6
1353	Organi istituzionali	\N	consuntivo-spese-impegni-spese-somma-funzioni-amministrazione-organi-istituzionali	1352	344	345	2	5
1352	Amministrazione	\N	consuntivo-spese-impegni-spese-somma-funzioni-amministrazione	1351	343	348	2	4
892	Piscine comunali	\N	consuntivo-spese-impegni-spese-correnti-funzioni-sport-piscine-comunali	891	197	198	2	6
1130	Teatri	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-cultura-teatri	1128	779	780	2	6
1362	Urbanistica e territorio	\N	consuntivo-spese-impegni-spese-somma-funzioni-territorio-e-ambiente-urbanistica-e-territorio	1361	362	363	2	5
1363	Edilizia pubblica	\N	consuntivo-spese-impegni-spese-somma-funzioni-territorio-e-ambiente-edilizia-pubblica	1361	364	365	2	5
738	Entrate extratributarie	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie	723	1330	1367	2	3
857	Entrate per conto terzi	\N	consuntivo-entrate-cassa-entrate-per-conto-terzi	813	1574	1575	2	3
1466	Residui attivi	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-competenza-residui-attivi	1449	31	32	2	4
1161	Cimiteri	\N	consuntivo-spese-cassa-spese-correnti-funzioni-sociale-cimiteri	1156	855	856	2	6
1168	Parchi	\N	consuntivo-spese-cassa-spese-correnti-funzioni-territorio-e-ambiente-parchi	1162	869	870	2	6
1170	Viabilità	\N	consuntivo-spese-cassa-spese-correnti-funzioni-viabilita-e-trasporti-viabilita	1169	873	874	2	6
1162	Territorio e ambiente	\N	consuntivo-spese-cassa-spese-correnti-funzioni-territorio-e-ambiente	1152	858	871	2	5
1345	Manifestazioni sportive	\N	consuntivo-spese-cassa-spese-somma-funzioni-sport-manifestazioni-sportive	1342	1186	1187	2	5
687	Altre Tasse	\N	consuntivo-entrate-accertamenti-imposte-e-tasse-tasse-altre-tasse	684	1220	1221	2	5
1471	Pagamenti	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-totale-pagamenti	1450	67	68	2	4
1472	Fondo di cassa al 31 dicembre	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-totale-fondo-di-cassa-al-31-dicembre	1450	65	66	2	4
1360	Cimiteri	\N	consuntivo-spese-impegni-spese-somma-funzioni-sociale-cimiteri	1355	358	359	2	5
1469	Fondo di cassa al 1° gennaio	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-totale-fondo-di-cassa-al-1°-gennaio	1450	63	64	2	4
1164	Edilizia pubblica	\N	consuntivo-spese-cassa-spese-correnti-funzioni-territorio-e-ambiente-edilizia-pubblica	1162	861	862	2	6
1165	Protezione civile	\N	consuntivo-spese-cassa-spese-correnti-funzioni-territorio-e-ambiente-protezione-civile	1162	863	864	2	6
1166	Servizio idrico	\N	consuntivo-spese-cassa-spese-correnti-funzioni-territorio-e-ambiente-servizio-idrico	1162	865	866	2	6
1477	Risultato di amministrazione = (6+7-8)	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-totale-risultato-di-amministrazione	1450	77	78	2	4
920	Protezione civile	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-territorio-e-ambiente-protezione-civile	917	253	254	2	6
1366	Rifiuti	\N	consuntivo-spese-impegni-spese-somma-funzioni-territorio-e-ambiente-rifiuti	1361	370	371	2	5
1361	Territorio e ambiente	\N	consuntivo-spese-impegni-spese-somma-funzioni-territorio-e-ambiente	1351	361	374	2	4
1055	funzioni	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni	1054	631	708	2	4
688	Altri tributi		consuntivo-entrate-accertamenti-imposte-e-tasse-tributi-speciali	679	1205	1206	2	4
1407	Finanziamenti a breve termine	\N	consuntivo-entrate-riscossioni-in-conto-competenza-prestiti-finanziamenti-a-breve-termine	766	1375	1376	2	4
1367	Parchi	\N	consuntivo-spese-impegni-spese-somma-funzioni-territorio-e-ambiente-parchi	1361	372	373	2	5
1369	Viabilità	\N	consuntivo-spese-impegni-spese-somma-funzioni-viabilita-e-trasporti-viabilita	1368	376	377	2	5
1370	Trasporti pubblici	\N	consuntivo-spese-impegni-spese-somma-funzioni-viabilita-e-trasporti-trasporti-pubblici	1368	378	379	2	5
1368	Viabilità e trasporti	\N	consuntivo-spese-impegni-spese-somma-funzioni-viabilita-e-trasporti	1351	375	382	2	4
1371	Illuminazione pubblica	\N	consuntivo-spese-impegni-spese-somma-funzioni-viabilita-e-trasporti-illuminazione-pubblica	1368	380	381	2	5
1026	Scuola materna	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-istruzione-scuola-materna	1025	557	558	2	6
1443	Concessioni di crediti e anticipazioni	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-interventi-concessioni-di-crediti-e-anticipazioni	1043	604	605	2	5
1214	Parchi	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-territorio-e-ambiente-parchi	1208	961	962	2	6
1227	Teatri	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-cultura-teatri	1225	987	988	2	6
901	Personale	\N	consuntivo-spese-impegni-spese-correnti-interventi-personale	900	216	217	2	5
1504	Debiti fuori bilancio	\N	consuntivo-riassuntivo-debiti-fuori-bilancio	1446	3	14	2	2
1505	Sentenze esecutive	\N	consuntivo-riassuntivo-debiti-fuori-bilancio-sentenze-esecutive	1504	12	13	2	3
1507	Ricapitalizzazione	\N	consuntivo-riassuntivo-debiti-fuori-bilancio-ricapitalizzazione	1504	10	11	2	3
1508	Procedure espropriative o di occupazione d'urgenza per opere di pubblica utilità	\N	consuntivo-riassuntivo-debiti-fuori-bilancio-procedure-espropriative-o-di-occupazione-d-urgenza-per-opere-di-pubblica-utilita	1504	8	9	2	3
1509	Acquisizione di Beni e Servizi	\N	consuntivo-riassuntivo-debiti-fuori-bilancio-acquisizione-di-beni-e-servizi	1504	4	5	2	3
859	Impegni	\N	consuntivo-spese-impegni	858	135	420	2	2
893	Stadio e altri impianti	\N	consuntivo-spese-impegni-spese-correnti-funzioni-sport-stadio-e-altri-impianti	891	199	200	2	6
1420	Quota capitale di mutui e prestiti	\N	consuntivo-spese-cassa-prestiti-quota-capitale-di-mutui-e-prestiti	1245	1037	1038	2	4
1422	Quota capitale di debiti pluriennali	\N	consuntivo-spese-cassa-prestiti-quota-capitale-di-debiti-pluriennali	1245	1035	1036	2	4
724	Imposte e tasse	\N	consuntivo-entrate-riscossioni-in-conto-competenza-imposte-e-tasse	723	1302	1321	2	3
754	Interessi su anticipazioni o crediti	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-interessi-su-anticipazioni-o-crediti	738	1361	1362	2	4
863	Organi istituzionali	\N	consuntivo-spese-impegni-spese-correnti-funzioni-amministrazione-organi-istituzionali	862	139	140	2	6
862	Amministrazione	\N	consuntivo-spese-impegni-spese-correnti-funzioni-amministrazione	861	138	143	2	5
908	Amministrazione	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-amministrazione	907	230	235	2	5
805	Trasferimenti dalla Regione	\N	consuntivo-entrate-riscossioni-in-conto-residui-vendite-e-trasferimenti-di-capitali-trasferimenti-dalla-regione	802	1483	1484	2	4
1157	Asili nido	\N	consuntivo-spese-cassa-spese-correnti-funzioni-sociale-asili-nido	1156	847	848	2	6
685	Rifiuti	\N	consuntivo-entrate-accertamenti-imposte-e-tasse-tasse-rifiuti	684	1216	1217	2	5
1084	Teatri	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-cultura-teatri	1082	687	688	2	6
1173	Istruzione	\N	consuntivo-spese-cassa-spese-correnti-funzioni-istruzione	1152	880	891	2	5
771	Casa e fabbricati	\N	consuntivo-entrate-riscossioni-in-conto-residui-imposte-e-tasse-imposte-casa-e-fabbricati	770	1404	1405	2	5
693	Entrate extratributarie	\N	consuntivo-entrate-accertamenti-entrate-extratributarie	678	1232	1269	2	3
751	Proventi di beni dell'ente	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-proventi-di-beni-dellente	738	1355	1360	2	4
1094	interventi	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-interventi	1054	709	720	2	4
1468	Risultato di amministrazione = (6+7-8)	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-competenza-risultato-di-amministrazione	1449	37	38	2	4
1219	Istruzione	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-istruzione	1198	972	983	2	5
876	Rifiuti	\N	consuntivo-spese-impegni-spese-correnti-funzioni-territorio-e-ambiente-rifiuti	871	165	166	2	6
676	Consuntivo	\N	consuntivo	\N	1	1596	2	0
1148	Prestiti	\N	consuntivo-spese-pagamenti-in-conto-residui-prestiti	1053	820	833	2	3
681	Casa e fabbricati	\N	consuntivo-entrate-accertamenti-imposte-e-tasse-imposte-casa-e-fabbricati	680	1208	1209	2	5
706	Proventi di beni dell'ente	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-proventi-di-beni-dellente	693	1257	1262	2	4
1244	Altri investimenti per interventi	\N	consuntivo-spese-cassa-spese-per-investimenti-interventi-altri-investimenti-per-interventi	1237	1024	1025	2	5
852	Trasferimenti di capitali da privati	\N	consuntivo-entrate-cassa-vendite-e-trasferimenti-di-capitali-trasferimenti-di-capitali-da-privati	847	1585	1590	2	4
1414	Anticipazioni di cassa	\N	consuntivo-entrate-cassa-prestiti-anticipazioni-di-cassa	856	1565	1566	2	4
1404	Assunzioni di mutui e prestiti	\N	consuntivo-entrate-accertamenti-prestiti-assunzioni-di-mutui-e-prestiti	721	1273	1274	2	4
937	Sport	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-sport	907	288	295	2	5
1418	Anticipazioni di cassa	\N	consuntivo-spese-cassa-prestiti-anticipazioni-di-cassa	1245	1029	1030	2	4
962	Sociale	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-sociale	958	430	441	2	5
770	Imposte	\N	consuntivo-entrate-riscossioni-in-conto-residui-imposte-e-tasse-imposte	769	1403	1410	2	4
755	Utili delle aziende partecipate	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-utili-delle-aziende-partecipate	738	1363	1364	2	4
1182	Sport	\N	consuntivo-spese-cassa-spese-correnti-funzioni-sport	1152	898	905	2	5
1150	Cassa	\N	consuntivo-spese-cassa	858	837	1200	2	2
1459	Risultato di amministrazione = (6+7-8)	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-residui-risultato-di-amministrazione	1448	57	58	2	4
871	Territorio e ambiente	\N	consuntivo-spese-impegni-spese-correnti-funzioni-territorio-e-ambiente	861	156	169	2	5
1384	Manifestazioni sportive	\N	consuntivo-spese-impegni-spese-somma-funzioni-sport-manifestazioni-sportive	1381	406	407	2	5
910	Amministrazione (altro)	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-amministrazione-amministrazione-altro	908	233	234	2	6
1386	Sviluppo economico	\N	consuntivo-spese-impegni-spese-somma-funzioni-sviluppo-economico	1351	411	412	2	4
1387	Servizi produttivi	\N	consuntivo-spese-impegni-spese-somma-funzioni-servizi-produttivi	1351	413	414	2	4
950	Partecipazioni azionarie	\N	consuntivo-spese-impegni-spese-per-investimenti-interventi-partecipazioni-azionarie	946	314	315	2	5
1074	Trasporti pubblici	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-viabilita-e-trasporti-trasporti-pubblici	1072	667	668	2	6
1052	Spese per conto terzi	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-conto-terzi	956	626	627	2	3
1057	Organi istituzionali	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-amministrazione-organi-istituzionali	1056	633	634	2	6
1056	Amministrazione	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-amministrazione	1055	632	637	2	5
1058	Amministrazione (altro)	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-amministrazione-amministrazione-altro	1056	635	636	2	6
1060	Asili nido	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-sociale-asili-nido	1059	639	640	2	6
847	Vendite e trasferimenti di capitali		consuntivo-entrate-cassa-vendite-e-trasferimenti-di-capitali	813	1576	1593	2	3
853	Permessi di costruire  e sanzioni	\N	consuntivo-entrate-cassa-vendite-e-trasferimenti-di-capitali-trasferimenti-di-capitali-da-privati-permessi-di-costruire-e-sanzioni	852	1586	1587	2	5
1423	Quota capitale per estinzione anticipata di prestiti	\N	consuntivo-spese-cassa-prestiti-quota-capitale-per-estinzione-anticipata-di-prestiti	1245	1039	1040	2	4
1221	Istruzione elementare	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-istruzione-istruzione-elementare	1219	975	976	2	6
707	Canone Occupazione Spazi e Aree Pubbliche	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-proventi-di-beni-dellente-canone-occupazione-spazi-e-aree-pubbliche	706	1258	1259	2	5
1328	Parchi	\N	consuntivo-spese-cassa-spese-somma-funzioni-territorio-e-ambiente-parchi	1322	1152	1153	2	5
1073	Viabilità	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-viabilita-e-trasporti-viabilita	1072	665	666	2	6
1053	Pagamenti in conto residui	\N	consuntivo-spese-pagamenti-in-conto-residui	858	629	836	2	2
941	Turismo	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-turismo	907	296	297	2	5
1131	Sport	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-sport	1101	782	789	2	5
822	Altre Tasse	\N	consuntivo-entrate-cassa-imposte-e-tasse-tasse-altre-tasse	819	1514	1515	2	5
911	Sociale	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-sociale	907	236	247	2	5
1112	Urbanistica e territorio	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-territorio-e-ambiente-urbanistica-e-territorio	1111	743	744	2	6
1143	Trasferimenti di capitale	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-interventi-trasferimenti-di-capitale	1140	806	807	2	5
1144	Partecipazioni azionarie	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-interventi-partecipazioni-azionarie	1140	808	809	2	5
1432	Quota capitale di mutui e prestiti	\N	consuntivo-spese-pagamenti-in-conto-competenza-prestiti-quota-capitale-di-mutui-e-prestiti	1051	621	622	2	4
748	Territorio e ambiente	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-servizi-pubblici-territorio-e-ambiente	739	1348	1349	2	5
739	Servizi pubblici	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-servizi-pubblici	738	1331	1354	2	4
1062	Residenze per anziani	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-sociale-residenze-per-anziani	1059	643	644	2	6
971	Protezione civile	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-territorio-e-ambiente-protezione-civile	968	447	448	2	6
972	Servizio idrico	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-territorio-e-ambiente-servizio-idrico	968	449	450	2	6
973	Rifiuti	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-territorio-e-ambiente-rifiuti	968	451	452	2	6
713	Alienazione del patrimonio	\N	consuntivo-entrate-accertamenti-vendite-e-trasferimenti-di-capitali-alienazione-del-patrimonio	712	1283	1284	2	4
833	Istruzione 	\N	consuntivo-entrate-cassa-entrate-extratributarie-servizi-pubblici-istruzione	829	1534	1535	2	5
1453	Pagamenti	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-residui-pagamenti	1448	47	48	2	4
1454	Fondo di cassa al 31 dicembre	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-residui-fondo-di-cassa-al-31-dicembre	1448	45	46	2	4
1447	Gestione finanziaria	\N	consuntivo-riassuntivo-gestione-finanziaria	1446	19	80	2	2
1450	Gestione totale	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-totale	1447	60	79	2	3
1455	Pagamenti per azioni esecutive non regolarizzate al 31.12	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-residui-pagamenti-per-azioni-esecutive-non-regolarizzate-al-31.12	1448	49	50	2	4
1456	Differenza	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-residui-differenza	1448	41	42	2	4
1457	Residui attivi	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-residui-residui-attivi	1448	51	52	2	4
1460	Fondo di cassa al 1° gennaio	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-competenza-fondo-di-cassa-al-1°-gennaio	1449	23	24	2	4
1461	Riscossioni	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-competenza-riscossioni	1449	35	36	2	4
1473	Pagamenti per azioni esecutive non regolarizzate al 31.12	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-totale-pagamenti-per-azioni-esecutive-non-regolarizzate-al-31.12	1450	69	70	2	4
1474	Differenza	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-totale-differenza	1450	61	62	2	4
1470	Riscossioni	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-totale-riscossioni	1450	75	76	2	4
1476	Residui passivi	\N	consuntivo-riassuntivo-gestione-finanziaria-gestione-totale-residui-passivi	1450	73	74	2	4
715	Trasferimenti dalla Regione	\N	consuntivo-entrate-accertamenti-vendite-e-trasferimenti-di-capitali-trasferimenti-dalla-regione	712	1287	1288	2	4
851	Trasferimenti da altri enti pubblici	\N	consuntivo-entrate-cassa-vendite-e-trasferimenti-di-capitali-trasferimenti-da-altri-enti-pubblici	847	1583	1584	2	4
850	Trasferimenti dalla Regione	\N	consuntivo-entrate-cassa-vendite-e-trasferimenti-di-capitali-trasferimenti-dalla-regione	847	1581	1582	2	4
1128	Cultura	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-cultura	1101	776	781	2	5
1132	Piscine comunali	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-sport-piscine-comunali	1131	783	784	2	6
912	Asili nido	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-sociale-asili-nido	911	237	238	2	6
913	Prevenzione e riabilitazione	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-sociale-prevenzione-e-riabilitazione	911	239	240	2	6
1071	Parchi	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-territorio-e-ambiente-parchi	1065	661	662	2	6
967	Cimiteri	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-sociale-cimiteri	962	439	440	2	6
969	Urbanistica e territorio	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-territorio-e-ambiente-urbanistica-e-territorio	968	443	444	2	6
970	Edilizia pubblica	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-territorio-e-ambiente-edilizia-pubblica	968	445	446	2	6
740	Amministrazione	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-servizi-pubblici-amministrazione	739	1332	1333	2	5
1406	Anticipazioni di cassa	\N	consuntivo-entrate-riscossioni-in-conto-competenza-prestiti-anticipazioni-di-cassa	766	1369	1370	2	4
787	Polizia locale	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-servizi-pubblici-polizia-locale	784	1434	1435	2	5
1133	Stadio e altri impianti	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-sport-stadio-e-altri-impianti	1131	785	786	2	6
1134	Manifestazioni sportive	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-sport-manifestazioni-sportive	1131	787	788	2	6
1135	Turismo	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-turismo	1101	790	791	2	5
1136	Sviluppo economico	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-sviluppo-economico	1101	792	793	2	5
1137	Servizi produttivi	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-servizi-produttivi	1101	794	795	2	5
1138	Polizia locale	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-polizia-locale	1101	796	797	2	5
1139	Giustizia	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-giustizia	1101	798	799	2	5
796	Proventi di beni dell'ente	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-proventi-di-beni-dellente	783	1453	1458	2	4
836	Turismo	\N	consuntivo-entrate-cassa-entrate-extratributarie-servizi-pubblici-turismo	829	1540	1541	2	5
1104	Amministrazione (altro)	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-amministrazione-amministrazione-altro	1102	727	728	2	6
1323	Urbanistica e territorio	\N	consuntivo-spese-cassa-spese-somma-funzioni-territorio-e-ambiente-urbanistica-e-territorio	1322	1142	1143	2	5
1373	Scuola materna	\N	consuntivo-spese-impegni-spese-somma-funzioni-istruzione-scuola-materna	1372	384	385	2	5
790	Sport	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-servizi-pubblici-sport	784	1440	1441	2	5
769	Imposte e tasse	\N	consuntivo-entrate-riscossioni-in-conto-residui-imposte-e-tasse	768	1400	1419	2	3
783	Entrate extratributarie	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie	768	1428	1465	2	3
1431	Finanziamenti a breve termine	\N	consuntivo-spese-pagamenti-in-conto-competenza-prestiti-finanziamenti-a-breve-termine	1051	615	616	2	4
845	Utili delle aziende partecipate	\N	consuntivo-entrate-cassa-entrate-extratributarie-utili-delle-aziende-partecipate	828	1559	1560	2	4
936	Teatri	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-cultura-teatri	934	285	286	2	6
1146	Conferimenti di capitale	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-interventi-conferimenti-di-capitale	1140	814	815	2	5
1100	Spese per investimenti	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti	1053	722	819	2	3
1082	Cultura	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-cultura	1055	684	689	2	5
780	Contributi e trasferimenti dallo Stato	\N	consuntivo-entrate-riscossioni-in-conto-residui-contributi-pubblici-contributi-dallo-stato	779	1421	1422	2	4
917	Territorio e ambiente	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-territorio-e-ambiente	907	248	261	2	5
923	Parchi	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-territorio-e-ambiente-parchi	917	259	260	2	6
829	Servizi pubblici	\N	consuntivo-entrate-cassa-entrate-extratributarie-servizi-pubblici	828	1527	1550	2	4
761	Trasferimenti da altri enti pubblici	\N	consuntivo-entrate-riscossioni-in-conto-competenza-vendite-e-trasferimenti-di-capitali-trasferimenti-da-altri-enti-pubblici	757	1387	1388	2	4
781	Contributi e trasferimenti dalla Regione	\N	consuntivo-entrate-riscossioni-in-conto-residui-contributi-pubblici-contributi-dalla-regione	779	1423	1424	2	4
697	Polizia locale	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-servizi-pubblici-polizia-locale	694	1238	1239	2	5
1108	Residenze per anziani	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-sociale-residenze-per-anziani	1105	735	736	2	6
1109	Assistenza, beneficenza e altro	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-sociale-assistenza-beneficenza-e-altro	1105	737	738	2	6
733	Altri tributi		consuntivo-entrate-riscossioni-in-conto-competenza-imposte-e-tasse-tributi-speciali	724	1303	1304	2	4
960	Organi istituzionali	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-amministrazione-organi-istituzionali	959	425	426	2	6
959	Amministrazione	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-amministrazione	958	424	429	2	5
961	Amministrazione (altro)	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-amministrazione-amministrazione-altro	959	427	428	2	6
778	Altri tributi		consuntivo-entrate-riscossioni-in-conto-residui-imposte-e-tasse-tributi-speciali	769	1401	1402	2	4
803	Alienazione del patrimonio	\N	consuntivo-entrate-riscossioni-in-conto-residui-vendite-e-trasferimenti-di-capitali-alienazione-del-patrimonio	802	1479	1480	2	4
831	Giustizia	\N	consuntivo-entrate-cassa-entrate-extratributarie-servizi-pubblici-giustizia	829	1530	1531	2	5
924	Viabilità e trasporti	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-viabilita-e-trasporti	907	262	269	2	5
927	Illuminazione pubblica	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-viabilita-e-trasporti-illuminazione-pubblica	924	267	268	2	6
929	Scuola materna	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-istruzione-scuola-materna	928	271	272	2	6
1140	interventi	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-interventi	1100	801	818	2	4
1147	Altri investimenti per interventi	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-interventi-altri-investimenti-per-interventi	1140	816	817	2	5
1204	Prevenzione e riabilitazione	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-sociale-prevenzione-e-riabilitazione	1202	941	942	2	6
1218	Illuminazione pubblica	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-viabilita-e-trasporti-illuminazione-pubblica	1215	969	970	2	6
799	Interessi su anticipazioni o crediti	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-interessi-su-anticipazioni-o-crediti	783	1459	1460	2	4
759	Trasferimenti dallo Stato	\N	consuntivo-entrate-riscossioni-in-conto-competenza-vendite-e-trasferimenti-di-capitali-trasferimenti-dallo-stato	757	1383	1384	2	4
711	Altre entrate extratributarie	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-altre-entrate-extratributarie	693	1267	1268	2	4
988	Sport	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-sport	958	482	489	2	5
1385	Turismo	\N	consuntivo-spese-impegni-spese-somma-funzioni-turismo	1351	409	410	2	4
905	Altre spese per interventi correnti	\N	consuntivo-spese-impegni-spese-correnti-interventi-altre-spese-per-interventi-correnti	900	224	225	2	5
881	Illuminazione pubblica	\N	consuntivo-spese-impegni-spese-correnti-funzioni-viabilita-e-trasporti-illuminazione-pubblica	878	175	176	2	6
883	Scuola materna	\N	consuntivo-spese-impegni-spese-correnti-funzioni-istruzione-scuola-materna	882	179	180	2	6
884	Istruzione elementare	\N	consuntivo-spese-impegni-spese-correnti-funzioni-istruzione-istruzione-elementare	882	181	182	2	6
885	Istruzione media	\N	consuntivo-spese-impegni-spese-correnti-funzioni-istruzione-istruzione-media	882	183	184	2	6
762	Trasferimenti di capitali da privati	\N	consuntivo-entrate-riscossioni-in-conto-competenza-vendite-e-trasferimenti-di-capitali-trasferimenti-di-capitali-da-privati	757	1389	1394	2	4
776	Occupazione suolo pubblico	\N	consuntivo-entrate-riscossioni-in-conto-residui-imposte-e-tasse-tasse-occupazione-suolo-pubblico	774	1414	1415	2	5
1324	Edilizia pubblica	\N	consuntivo-spese-cassa-spese-somma-funzioni-territorio-e-ambiente-edilizia-pubblica	1322	1144	1145	2	5
807	Trasferimenti di capitali da privati	\N	consuntivo-entrate-riscossioni-in-conto-residui-vendite-e-trasferimenti-di-capitali-trasferimenti-di-capitali-da-privati	802	1487	1492	2	4
1379	Biblioteche e musei	\N	consuntivo-spese-impegni-spese-somma-funzioni-cultura-biblioteche-e-musei	1378	396	397	2	5
968	Territorio e ambiente	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-territorio-e-ambiente	958	442	455	2	5
1061	Prevenzione e riabilitazione	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-sociale-prevenzione-e-riabilitazione	1059	641	642	2	6
1388	Polizia locale	\N	consuntivo-spese-impegni-spese-somma-funzioni-polizia-locale	1351	415	416	2	4
1172	Illuminazione pubblica	\N	consuntivo-spese-cassa-spese-correnti-funzioni-viabilita-e-trasporti-illuminazione-pubblica	1169	877	878	2	6
837	Viabilità e trasporti	\N	consuntivo-entrate-cassa-entrate-extratributarie-servizi-pubblici-viabilita-e-trasporti	829	1542	1543	2	5
1437	Finanziamenti a breve termine	\N	consuntivo-spese-pagamenti-in-conto-residui-prestiti-finanziamenti-a-breve-termine	1148	823	824	2	4
1207	Cimiteri	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-sociale-cimiteri	1202	947	948	2	6
1206	Assistenza, beneficenza e altro	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-sociale-assistenza-beneficenza-e-altro	1202	945	946	2	6
1224	Assistenza, trasporto, mense	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-istruzione-assistenza-trasporto-mense	1219	981	982	2	6
896	Sviluppo economico	\N	consuntivo-spese-impegni-spese-correnti-funzioni-sviluppo-economico	861	206	207	2	5
897	Servizi produttivi	\N	consuntivo-spese-impegni-spese-correnti-funzioni-servizi-produttivi	861	208	209	2	5
1189	Polizia locale	\N	consuntivo-spese-cassa-spese-correnti-funzioni-polizia-locale	1152	912	913	2	5
764	Trasferimenti di capitali (altro )	\N	consuntivo-entrate-riscossioni-in-conto-competenza-vendite-e-trasferimenti-di-capitali-trasferimenti-di-capitali-da-privati-trasferimenti-di-capitali-altro	762	1392	1393	2	5
1174	Scuola materna	\N	consuntivo-spese-cassa-spese-correnti-funzioni-istruzione-scuola-materna	1173	881	882	2	6
1175	Istruzione elementare	\N	consuntivo-spese-cassa-spese-correnti-funzioni-istruzione-istruzione-elementare	1173	883	884	2	6
1176	Istruzione media	\N	consuntivo-spese-cassa-spese-correnti-funzioni-istruzione-istruzione-media	1173	885	886	2	6
918	Urbanistica e territorio	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-territorio-e-ambiente-urbanistica-e-territorio	917	249	250	2	6
698	Istruzione 	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-servizi-pubblici-istruzione	694	1240	1241	2	5
951	Acquisizioni di beni mobili	\N	consuntivo-spese-impegni-spese-per-investimenti-interventi-acquisizioni-di-beni-mobili	946	316	317	2	5
1184	Stadio e altri impianti	\N	consuntivo-spese-cassa-spese-correnti-funzioni-sport-stadio-e-altri-impianti	1182	901	902	2	6
1141	Acquisizione di beni immobili	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-interventi-acquisizione-di-beni-immobili	1140	802	803	2	5
789	Cultura	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-servizi-pubblici-cultura	784	1438	1439	2	5
752	Canone Occupazione Spazi e Aree Pubbliche	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-proventi-di-beni-dellente-canone-occupazione-spazi-e-aree-pubbliche	751	1356	1357	2	5
1429	Quota capitale per estinzione anticipata di prestiti	\N	consuntivo-spese-impegni-prestiti-quota-capitale-per-estinzione-anticipata-di-prestiti	954	337	338	2	4
1193	Prestazioni di servizi	\N	consuntivo-spese-cassa-spese-correnti-interventi-prestazioni-di-servizi	1191	920	921	2	5
1409	Emissioni di prestiti obbligazionari	\N	consuntivo-entrate-riscossioni-in-conto-competenza-prestiti-emissioni-di-prestiti-obbligazionari	766	1373	1374	2	4
1410	Anticipazioni di cassa	\N	consuntivo-entrate-riscossioni-in-conto-residui-prestiti-anticipazioni-di-cassa	811	1467	1468	2	4
846	Altre entrate extratributarie	\N	consuntivo-entrate-cassa-entrate-extratributarie-altre-entrate-extratributarie	828	1561	1562	2	4
810	Riscossioni di crediti	\N	consuntivo-entrate-riscossioni-in-conto-residui-vendite-e-trasferimenti-di-capitali-riscossioni-di-crediti	802	1493	1494	2	4
838	Territorio e ambiente	\N	consuntivo-entrate-cassa-entrate-extratributarie-servizi-pubblici-territorio-e-ambiente	829	1544	1545	2	5
806	Trasferimenti da altri enti pubblici	\N	consuntivo-entrate-riscossioni-in-conto-residui-vendite-e-trasferimenti-di-capitali-trasferimenti-da-altri-enti-pubblici	802	1485	1486	2	4
844	Interessi su anticipazioni o crediti	\N	consuntivo-entrate-cassa-entrate-extratributarie-interessi-su-anticipazioni-o-crediti	828	1557	1558	2	4
1411	Finanziamenti a breve termine	\N	consuntivo-entrate-riscossioni-in-conto-residui-prestiti-finanziamenti-a-breve-termine	811	1473	1474	2	4
1413	Emissioni di prestiti obbligazionari	\N	consuntivo-entrate-riscossioni-in-conto-residui-prestiti-emissioni-di-prestiti-obbligazionari	811	1471	1472	2	4
854	Trasferimenti di capitali (altro )	\N	consuntivo-entrate-cassa-vendite-e-trasferimenti-di-capitali-trasferimenti-di-capitali-da-privati-trasferimenti-di-capitali-altro	852	1588	1589	2	5
849	Trasferimenti dallo Stato	\N	consuntivo-entrate-cassa-vendite-e-trasferimenti-di-capitali-trasferimenti-dallo-stato	847	1579	1580	2	4
1415	Finanziamenti a breve termine	\N	consuntivo-entrate-cassa-prestiti-finanziamenti-a-breve-termine	856	1571	1572	2	4
708	Altri proventi	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-proventi-di-beni-dellente-altri-proventi	706	1260	1261	2	5
880	Trasporti pubblici	\N	consuntivo-spese-impegni-spese-correnti-funzioni-viabilita-e-trasporti-trasporti-pubblici	878	173	174	2	6
864	Amministrazione (altro)	\N	consuntivo-spese-impegni-spese-correnti-funzioni-amministrazione-amministrazione-altro	862	141	142	2	6
745	Sport	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-servizi-pubblici-sport	739	1342	1343	2	5
741	Giustizia	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-servizi-pubblici-giustizia	739	1334	1335	2	5
756	Altre entrate extratributarie	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-altre-entrate-extratributarie	738	1365	1366	2	4
731	Occupazione suolo pubblico	\N	consuntivo-entrate-riscossioni-in-conto-competenza-imposte-e-tasse-tasse-occupazione-suolo-pubblico	729	1316	1317	2	5
940	Manifestazioni sportive	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-sport-manifestazioni-sportive	937	293	294	2	6
1408	Assunzioni di mutui e prestiti	\N	consuntivo-entrate-riscossioni-in-conto-competenza-prestiti-assunzioni-di-mutui-e-prestiti	766	1371	1372	2	4
1233	Sviluppo economico	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-sviluppo-economico	1198	1000	1001	2	5
1234	Servizi produttivi	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-servizi-produttivi	1198	1002	1003	2	5
1213	Rifiuti	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-territorio-e-ambiente-rifiuti	1208	959	960	2	6
1220	Scuola materna	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-istruzione-scuola-materna	1219	973	974	2	6
1223	Istruzione secondaria superiore	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-istruzione-istruzione-secondaria-superiore	1219	979	980	2	6
1063	Assistenza, beneficenza e altro	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-sociale-assistenza-beneficenza-e-altro	1059	645	646	2	6
1059	Sociale	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-sociale	1055	638	649	2	5
1197	Spese per investimenti	\N	consuntivo-spese-cassa-spese-per-investimenti	1150	930	1027	2	3
712	Vendite e trasferimenti di capitali		consuntivo-entrate-accertamenti-vendite-e-trasferimenti-di-capitali	678	1282	1299	2	3
809	Trasferimenti di capitali (altro )	\N	consuntivo-entrate-riscossioni-in-conto-residui-vendite-e-trasferimenti-di-capitali-trasferimenti-di-capitali-da-privati-trasferimenti-di-capitali-altro	807	1490	1491	2	5
692	Contributi e trasferimenti da altri enti pubblici	\N	consuntivo-entrate-accertamenti-contributi-pubblici-contributi-da-altri-enti-pubblici	689	1229	1230	2	4
1347	Sviluppo economico	\N	consuntivo-spese-cassa-spese-somma-funzioni-sviluppo-economico	1312	1191	1192	2	4
1348	Servizi produttivi	\N	consuntivo-spese-cassa-spese-somma-funzioni-servizi-produttivi	1312	1193	1194	2	4
683	Imposte (altro)	\N	consuntivo-entrate-accertamenti-imposte-e-tasse-imposte-imposte-altro	680	1212	1213	2	5
1343	Piscine comunali	\N	consuntivo-spese-cassa-spese-somma-funzioni-sport-piscine-comunali	1342	1182	1183	2	5
696	Giustizia	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-servizi-pubblici-giustizia	694	1236	1237	2	5
1325	Protezione civile	\N	consuntivo-spese-cassa-spese-somma-funzioni-territorio-e-ambiente-protezione-civile	1322	1146	1147	2	5
1445	Concessioni di crediti e anticipazioni	\N	consuntivo-spese-cassa-spese-per-investimenti-interventi-concessioni-di-crediti-e-anticipazioni	1237	1020	1021	2	5
1230	Stadio e altri impianti	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-sport-stadio-e-altri-impianti	1228	993	994	2	6
1064	Cimiteri	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-sociale-cimiteri	1059	647	648	2	6
1101	funzioni	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni	1100	723	800	2	4
1066	Urbanistica e territorio	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-territorio-e-ambiente-urbanistica-e-territorio	1065	651	652	2	6
1067	Edilizia pubblica	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-territorio-e-ambiente-edilizia-pubblica	1065	653	654	2	6
976	Viabilità	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-viabilita-e-trasporti-viabilita	975	457	458	2	6
1231	Manifestazioni sportive	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-sport-manifestazioni-sportive	1228	995	996	2	6
1377	Assistenza, trasporto, mense	\N	consuntivo-spese-impegni-spese-somma-funzioni-istruzione-assistenza-trasporto-mense	1372	392	393	2	5
825	Contributi e trasferimenti dallo Stato	\N	consuntivo-entrate-cassa-contributi-pubblici-contributi-dallo-stato	824	1519	1520	2	4
1344	Stadio e altri impianti	\N	consuntivo-spese-cassa-spese-somma-funzioni-sport-stadio-e-altri-impianti	1342	1184	1185	2	5
1028	Istruzione media	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-istruzione-istruzione-media	1025	561	562	2	6
1114	Protezione civile	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-territorio-e-ambiente-protezione-civile	1111	747	748	2	6
1115	Servizio idrico	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-territorio-e-ambiente-servizio-idrico	1111	749	750	2	6
1116	Rifiuti	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-territorio-e-ambiente-rifiuti	1111	751	752	2	6
1111	Territorio e ambiente	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-territorio-e-ambiente	1101	742	755	2	5
1107	Prevenzione e riabilitazione	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-sociale-prevenzione-e-riabilitazione	1105	733	734	2	6
938	Piscine comunali	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-sport-piscine-comunali	937	289	290	2	6
939	Stadio e altri impianti	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-sport-stadio-e-altri-impianti	937	291	292	2	6
686	Occupazione suolo pubblico	\N	consuntivo-entrate-accertamenti-imposte-e-tasse-tasse-occupazione-suolo-pubblico	684	1218	1219	2	5
703	Territorio e ambiente	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-servizi-pubblici-territorio-e-ambiente	694	1250	1251	2	5
1123	Scuola materna	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-istruzione-scuola-materna	1122	765	766	2	6
744	Cultura	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-servizi-pubblici-cultura	739	1340	1341	2	5
1124	Istruzione elementare	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-istruzione-istruzione-elementare	1122	767	768	2	6
1125	Istruzione media	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-istruzione-istruzione-media	1122	769	770	2	6
1126	Istruzione secondaria superiore	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-istruzione-istruzione-secondaria-superiore	1122	771	772	2	6
1338	Assistenza, trasporto, mense	\N	consuntivo-spese-cassa-spese-somma-funzioni-istruzione-assistenza-trasporto-mense	1333	1172	1173	2	5
930	Istruzione elementare	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-istruzione-istruzione-elementare	928	273	274	2	6
931	Istruzione media	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-istruzione-istruzione-media	928	275	276	2	6
932	Istruzione secondaria superiore	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-istruzione-istruzione-secondaria-superiore	928	277	278	2	6
914	Residenze per anziani	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-sociale-residenze-per-anziani	911	241	242	2	6
915	Assistenza, beneficenza e altro	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-sociale-assistenza-beneficenza-e-altro	911	243	244	2	6
1120	Trasporti pubblici	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-viabilita-e-trasporti-trasporti-pubblici	1118	759	760	2	6
1354	Amministrazione (altro)	\N	consuntivo-spese-impegni-spese-somma-funzioni-amministrazione-amministrazione-altro	1352	346	347	2	5
1383	Stadio e altri impianti	\N	consuntivo-spese-impegni-spese-somma-funzioni-sport-stadio-e-altri-impianti	1381	404	405	2	5
1209	Urbanistica e territorio	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-territorio-e-ambiente-urbanistica-e-territorio	1208	951	952	2	6
1210	Edilizia pubblica	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-territorio-e-ambiente-edilizia-pubblica	1208	953	954	2	6
1113	Edilizia pubblica	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-territorio-e-ambiente-edilizia-pubblica	1111	745	746	2	6
1044	Acquisizione di beni immobili	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-interventi-acquisizione-di-beni-immobili	1043	594	595	2	5
1045	Incarichi professionali esterni	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-interventi-incarichi-professionali-esterni	1043	596	597	2	5
1159	Residenze per anziani	\N	consuntivo-spese-cassa-spese-correnti-funzioni-sociale-residenze-per-anziani	1156	851	852	2	6
725	Imposte	\N	consuntivo-entrate-riscossioni-in-conto-competenza-imposte-e-tasse-imposte	724	1305	1312	2	4
1047	Partecipazioni azionarie	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-interventi-partecipazioni-azionarie	1043	600	601	2	5
1048	Acquisizioni di beni mobili	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-interventi-acquisizioni-di-beni-mobili	1043	602	603	2	5
821	Occupazione suolo pubblico	\N	consuntivo-entrate-cassa-imposte-e-tasse-tasse-occupazione-suolo-pubblico	819	1512	1513	2	5
1376	Istruzione secondaria superiore	\N	consuntivo-spese-impegni-spese-somma-funzioni-istruzione-istruzione-secondaria-superiore	1372	390	391	2	5
1359	Assistenza, beneficenza e altro	\N	consuntivo-spese-impegni-spese-somma-funzioni-sociale-assistenza-beneficenza-e-altro	1355	356	357	2	5
1332	Illuminazione pubblica	\N	consuntivo-spese-cassa-spese-somma-funzioni-viabilita-e-trasporti-illuminazione-pubblica	1329	1160	1161	2	5
1335	Istruzione elementare	\N	consuntivo-spese-cassa-spese-somma-funzioni-istruzione-istruzione-elementare	1333	1166	1167	2	5
742	Polizia locale	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-servizi-pubblici-polizia-locale	739	1336	1337	2	5
750	Altri servizi	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-servizi-pubblici-altri-servizi	739	1352	1353	2	5
743	Istruzione 	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-servizi-pubblici-istruzione	739	1338	1339	2	5
1118	Viabilità e trasporti	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-viabilita-e-trasporti	1101	756	763	2	5
1121	Illuminazione pubblica	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-viabilita-e-trasporti-illuminazione-pubblica	1118	761	762	2	6
1142	Incarichi professionali esterni	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-interventi-incarichi-professionali-esterni	1140	804	805	2	5
925	Viabilità	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-viabilita-e-trasporti-viabilita	924	263	264	2	6
944	Polizia locale	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-polizia-locale	907	302	303	2	5
945	Giustizia	\N	consuntivo-spese-impegni-spese-per-investimenti-funzioni-giustizia	907	304	305	2	5
947	Acquisizione di beni immobili	\N	consuntivo-spese-impegni-spese-per-investimenti-interventi-acquisizione-di-beni-immobili	946	308	309	2	5
948	Incarichi professionali esterni	\N	consuntivo-spese-impegni-spese-per-investimenti-interventi-incarichi-professionali-esterni	946	310	311	2	5
949	Trasferimenti di capitale	\N	consuntivo-spese-impegni-spese-per-investimenti-interventi-trasferimenti-di-capitale	946	312	313	2	5
872	Urbanistica e territorio	\N	consuntivo-spese-impegni-spese-correnti-funzioni-territorio-e-ambiente-urbanistica-e-territorio	871	157	158	2	6
1188	Servizi produttivi	\N	consuntivo-spese-cassa-spese-correnti-funzioni-servizi-produttivi	1152	910	911	2	5
1435	Quota capitale per estinzione anticipata di prestiti	\N	consuntivo-spese-pagamenti-in-conto-competenza-prestiti-quota-capitale-per-estinzione-anticipata-di-prestiti	1051	623	624	2	4
737	Contributi e trasferimenti da altri enti pubblici	\N	consuntivo-entrate-riscossioni-in-conto-competenza-contributi-pubblici-contributi-da-altri-enti-pubblici	734	1327	1328	2	4
1428	Quota capitale di debiti pluriennali	\N	consuntivo-spese-impegni-prestiti-quota-capitale-di-debiti-pluriennali	954	333	334	2	4
1382	Piscine comunali	\N	consuntivo-spese-impegni-spese-somma-funzioni-sport-piscine-comunali	1381	402	403	2	5
1322	Territorio e ambiente	\N	consuntivo-spese-cassa-spese-somma-funzioni-territorio-e-ambiente	1312	1141	1154	2	4
695	Amministrazione	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-servizi-pubblici-amministrazione	694	1234	1235	2	5
817	Addizionale IRPEF	\N	consuntivo-entrate-cassa-imposte-e-tasse-imposte-addizionale-irpef	815	1504	1505	2	5
963	Asili nido	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-sociale-asili-nido	962	431	432	2	6
964	Prevenzione e riabilitazione	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-sociale-prevenzione-e-riabilitazione	962	433	434	2	6
1375	Istruzione media	\N	consuntivo-spese-impegni-spese-somma-funzioni-istruzione-istruzione-media	1372	388	389	2	5
1242	Acquisizioni di beni mobili	\N	consuntivo-spese-cassa-spese-per-investimenti-interventi-acquisizioni-di-beni-mobili	1237	1018	1019	2	5
729	Tasse	\N	consuntivo-entrate-riscossioni-in-conto-competenza-imposte-e-tasse-tasse	724	1313	1320	2	4
719	Trasferimenti di capitali (altro )	\N	consuntivo-entrate-accertamenti-vendite-e-trasferimenti-di-capitali-trasferimenti-di-capitali-da-privati-trasferimenti-di-capitali-altro	717	1294	1295	2	5
726	Casa e fabbricati	\N	consuntivo-entrate-riscossioni-in-conto-competenza-imposte-e-tasse-imposte-casa-e-fabbricati	725	1306	1307	2	5
717	Trasferimenti di capitali da privati	\N	consuntivo-entrate-accertamenti-vendite-e-trasferimenti-di-capitali-trasferimenti-di-capitali-da-privati	712	1291	1296	2	4
1424	Anticipazioni di cassa	\N	consuntivo-spese-impegni-prestiti-anticipazioni-di-cassa	954	327	328	2	4
974	Parchi	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-territorio-e-ambiente-parchi	968	453	454	2	6
757	Vendite e trasferimenti di capitali		consuntivo-entrate-riscossioni-in-conto-competenza-vendite-e-trasferimenti-di-capitali	723	1380	1397	2	3
797	Canone Occupazione Spazi e Aree Pubbliche	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-proventi-di-beni-dellente-canone-occupazione-spazi-e-aree-pubbliche	796	1454	1455	2	5
1049	Conferimenti di capitale	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-interventi-conferimenti-di-capitale	1043	606	607	2	5
1417	Emissioni di prestiti obbligazionari	\N	consuntivo-entrate-cassa-prestiti-emissioni-di-prestiti-obbligazionari	856	1569	1570	2	4
830	Amministrazione	\N	consuntivo-entrate-cassa-entrate-extratributarie-servizi-pubblici-amministrazione	829	1528	1529	2	5
732	Altre Tasse	\N	consuntivo-entrate-riscossioni-in-conto-competenza-imposte-e-tasse-tasse-altre-tasse	729	1318	1319	2	5
793	Territorio e ambiente	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-servizi-pubblici-territorio-e-ambiente	784	1446	1447	2	5
758	Alienazione del patrimonio	\N	consuntivo-entrate-riscossioni-in-conto-competenza-vendite-e-trasferimenti-di-capitali-alienazione-del-patrimonio	757	1381	1382	2	4
792	Viabilità e trasporti	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-servizi-pubblici-viabilita-e-trasporti	784	1444	1445	2	5
786	Giustizia	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-servizi-pubblici-giustizia	784	1432	1433	2	5
765	Riscossioni di crediti	\N	consuntivo-entrate-riscossioni-in-conto-competenza-vendite-e-trasferimenti-di-capitali-riscossioni-di-crediti	757	1395	1396	2	4
800	Utili delle aziende partecipate	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-utili-delle-aziende-partecipate	783	1461	1462	2	4
788	Istruzione 	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-servizi-pubblici-istruzione	784	1436	1437	2	5
694	Servizi pubblici	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-servizi-pubblici	693	1233	1256	2	4
746	Turismo	\N	consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-servizi-pubblici-turismo	739	1344	1345	2	5
1403	Finanziamenti a breve termine	\N	consuntivo-entrate-accertamenti-prestiti-finanziamenti-a-breve-termine	721	1277	1278	2	4
1405	Emissioni di prestiti obbligazionari	\N	consuntivo-entrate-accertamenti-prestiti-emissioni-di-prestiti-obbligazionari	721	1275	1276	2	4
785	Amministrazione	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-servizi-pubblici-amministrazione	784	1430	1431	2	5
798	Altri proventi	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-proventi-di-beni-dellente-altri-proventi	796	1456	1457	2	5
794	Sociale	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-servizi-pubblici-sociale	784	1448	1449	2	5
784	Servizi pubblici	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-servizi-pubblici	783	1429	1452	2	4
804	Trasferimenti dallo Stato	\N	consuntivo-entrate-riscossioni-in-conto-residui-vendite-e-trasferimenti-di-capitali-trasferimenti-dallo-stato	802	1481	1482	2	4
1337	Istruzione secondaria superiore	\N	consuntivo-spese-cassa-spese-somma-funzioni-istruzione-istruzione-secondaria-superiore	1333	1170	1171	2	5
704	Sociale	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-servizi-pubblici-sociale	694	1252	1253	2	5
1205	Residenze per anziani	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-sociale-residenze-per-anziani	1202	943	944	2	6
1208	Territorio e ambiente	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-territorio-e-ambiente	1198	950	963	2	5
1177	Istruzione secondaria superiore	\N	consuntivo-spese-cassa-spese-correnti-funzioni-istruzione-istruzione-secondaria-superiore	1173	887	888	2	6
1178	Assistenza, trasporto, mense	\N	consuntivo-spese-cassa-spese-correnti-funzioni-istruzione-assistenza-trasporto-mense	1173	889	890	2	6
1180	Biblioteche e musei	\N	consuntivo-spese-cassa-spese-correnti-funzioni-cultura-biblioteche-e-musei	1179	893	894	2	6
1201	Amministrazione (altro)	\N	consuntivo-spese-cassa-spese-per-investimenti-funzioni-amministrazione-amministrazione-altro	1199	935	936	2	6
1441	Quota capitale per estinzione anticipata di prestiti	\N	consuntivo-spese-pagamenti-in-conto-residui-prestiti-quota-capitale-per-estinzione-anticipata-di-prestiti	1148	831	832	2	4
1444	Concessioni di crediti e anticipazioni	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-interventi-concessioni-di-crediti-e-anticipazioni	1140	812	813	2	5
834	Cultura	\N	consuntivo-entrate-cassa-entrate-extratributarie-servizi-pubblici-cultura	829	1536	1537	2	5
808	Permessi di costruire  e sanzioni	\N	consuntivo-entrate-riscossioni-in-conto-residui-vendite-e-trasferimenti-di-capitali-trasferimenti-di-capitali-da-privati-permessi-di-costruire-e-sanzioni	807	1488	1489	2	5
1318	Prevenzione e riabilitazione	\N	consuntivo-spese-cassa-spese-somma-funzioni-sociale-prevenzione-e-riabilitazione	1316	1132	1133	2	5
682	Addizionale IRPEF	\N	consuntivo-entrate-accertamenti-imposte-e-tasse-imposte-addizionale-irpef	680	1210	1211	2	5
722	Entrate per conto terzi	\N	consuntivo-entrate-accertamenti-entrate-per-conto-terzi	678	1280	1281	2	3
1320	Assistenza, beneficenza e altro	\N	consuntivo-spese-cassa-spese-somma-funzioni-sociale-assistenza-beneficenza-e-altro	1316	1136	1137	2	5
690	Contributi e trasferimenti dallo Stato	\N	consuntivo-entrate-accertamenti-contributi-pubblici-contributi-dallo-stato	689	1225	1226	2	4
702	Viabilità e trasporti	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-servizi-pubblici-viabilita-e-trasporti	694	1248	1249	2	5
710	Utili delle aziende partecipate	\N	consuntivo-entrate-accertamenti-entrate-extratributarie-utili-delle-aziende-partecipate	693	1265	1266	2	4
718	Permessi di costruire  e sanzioni	\N	consuntivo-entrate-accertamenti-vendite-e-trasferimenti-di-capitali-trasferimenti-di-capitali-da-privati-permessi-di-costruire-e-sanzioni	717	1292	1293	2	5
773	Imposte (altro)	\N	consuntivo-entrate-riscossioni-in-conto-residui-imposte-e-tasse-imposte-imposte-altro	770	1408	1409	2	5
795	Altri servizi	\N	consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie-servizi-pubblici-altri-servizi	784	1450	1451	2	5
772	Addizionale IRPEF	\N	consuntivo-entrate-riscossioni-in-conto-residui-imposte-e-tasse-imposte-addizionale-irpef	770	1406	1407	2	5
1027	Istruzione elementare	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-istruzione-istruzione-elementare	1025	559	560	2	6
1029	Istruzione secondaria superiore	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-istruzione-istruzione-secondaria-superiore	1025	563	564	2	6
1030	Assistenza, trasporto, mense	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-istruzione-assistenza-trasporto-mense	1025	565	566	2	6
1032	Biblioteche e musei	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-cultura-biblioteche-e-musei	1031	569	570	2	6
1031	Cultura	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-cultura	1004	568	573	2	5
1194	Trasferimenti	\N	consuntivo-spese-cassa-spese-correnti-interventi-trasferimenti	1191	922	923	2	5
1195	Interessi passivi e oneri finanziari diversi	\N	consuntivo-spese-cassa-spese-correnti-interventi-interessi-passivi-e-oneri-finanziari-diversi	1191	924	925	2	5
841	Proventi di beni dell'ente	\N	consuntivo-entrate-cassa-entrate-extratributarie-proventi-di-beni-dellente	828	1551	1556	2	4
977	Trasporti pubblici	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-viabilita-e-trasporti-trasporti-pubblici	975	459	460	2	6
975	Viabilità e trasporti	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-viabilita-e-trasporti	958	456	463	2	5
978	Illuminazione pubblica	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-viabilita-e-trasporti-illuminazione-pubblica	975	461	462	2	6
980	Scuola materna	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-istruzione-scuola-materna	979	465	466	2	6
981	Istruzione elementare	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-istruzione-istruzione-elementare	979	467	468	2	6
982	Istruzione media	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-istruzione-istruzione-media	979	469	470	2	6
983	Istruzione secondaria superiore	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-istruzione-istruzione-secondaria-superiore	979	471	472	2	6
979	Istruzione	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-istruzione	958	464	475	2	5
984	Assistenza, trasporto, mense	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-istruzione-assistenza-trasporto-mense	979	473	474	2	6
986	Biblioteche e musei	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-cultura-biblioteche-e-musei	985	477	478	2	6
989	Piscine comunali	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-sport-piscine-comunali	988	483	484	2	6
1090	Sviluppo economico	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-sviluppo-economico	1055	700	701	2	5
990	Stadio e altri impianti	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-sport-stadio-e-altri-impianti	988	485	486	2	6
991	Manifestazioni sportive	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-sport-manifestazioni-sportive	988	487	488	2	6
992	Turismo	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-turismo	958	490	491	2	5
993	Sviluppo economico	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-sviluppo-economico	958	492	493	2	5
994	Servizi produttivi	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-servizi-produttivi	958	494	495	2	5
996	Giustizia	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni-giustizia	958	498	499	2	5
998	Personale	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-interventi-personale	997	502	503	2	5
999	Prestazioni di servizi	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-interventi-prestazioni-di-servizi	997	504	505	2	5
1000	Trasferimenti	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-interventi-trasferimenti	997	506	507	2	5
1001	Interessi passivi e oneri finanziari diversi	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-interventi-interessi-passivi-e-oneri-finanziari-diversi	997	508	509	2	5
997	interventi	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-interventi	957	501	512	2	4
1158	Prevenzione e riabilitazione	\N	consuntivo-spese-cassa-spese-correnti-funzioni-sociale-prevenzione-e-riabilitazione	1156	849	850	2	6
1002	Altre spese per interventi correnti	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-interventi-altre-spese-per-interventi-correnti	997	510	511	2	5
1006	Organi istituzionali	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-amministrazione-organi-istituzionali	1005	517	518	2	6
1005	Amministrazione	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-amministrazione	1004	516	521	2	5
1007	Amministrazione (altro)	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-amministrazione-amministrazione-altro	1005	519	520	2	6
1009	Asili nido	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-sociale-asili-nido	1008	523	524	2	6
1008	Sociale	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-sociale	1004	522	533	2	5
1010	Prevenzione e riabilitazione	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-sociale-prevenzione-e-riabilitazione	1008	525	526	2	6
1011	Residenze per anziani	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-sociale-residenze-per-anziani	1008	527	528	2	6
1012	Assistenza, beneficenza e altro	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-sociale-assistenza-beneficenza-e-altro	1008	529	530	2	6
1013	Cimiteri	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-sociale-cimiteri	1008	531	532	2	6
1015	Urbanistica e territorio	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-territorio-e-ambiente-urbanistica-e-territorio	1014	535	536	2	6
1016	Edilizia pubblica	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-territorio-e-ambiente-edilizia-pubblica	1014	537	538	2	6
1017	Protezione civile	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-territorio-e-ambiente-protezione-civile	1014	539	540	2	6
1018	Servizio idrico	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-territorio-e-ambiente-servizio-idrico	1014	541	542	2	6
1019	Rifiuti	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-territorio-e-ambiente-rifiuti	1014	543	544	2	6
1014	Territorio e ambiente	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-territorio-e-ambiente	1004	534	547	2	5
1033	Teatri	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-cultura-teatri	1031	571	572	2	6
1004	funzioni	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni	1003	515	592	2	4
1035	Piscine comunali	\N	consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni-sport-piscine-comunali	1034	575	576	2	6
1072	Viabilità e trasporti	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-viabilita-e-trasporti	1055	664	671	2	5
1075	Illuminazione pubblica	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-viabilita-e-trasporti-illuminazione-pubblica	1072	669	670	2	6
1077	Scuola materna	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-istruzione-scuola-materna	1076	673	674	2	6
1078	Istruzione elementare	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-istruzione-istruzione-elementare	1076	675	676	2	6
1079	Istruzione media	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-istruzione-istruzione-media	1076	677	678	2	6
1080	Istruzione secondaria superiore	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-istruzione-istruzione-secondaria-superiore	1076	679	680	2	6
1081	Assistenza, trasporto, mense	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-istruzione-assistenza-trasporto-mense	1076	681	682	2	6
1083	Biblioteche e musei	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-cultura-biblioteche-e-musei	1082	685	686	2	6
1086	Piscine comunali	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-sport-piscine-comunali	1085	691	692	2	6
1087	Stadio e altri impianti	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-sport-stadio-e-altri-impianti	1085	693	694	2	6
1088	Manifestazioni sportive	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-sport-manifestazioni-sportive	1085	695	696	2	6
1089	Turismo	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-turismo	1055	698	699	2	5
1091	Servizi produttivi	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-servizi-produttivi	1055	702	703	2	5
1092	Polizia locale	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-polizia-locale	1055	704	705	2	5
1093	Giustizia	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni-giustizia	1055	706	707	2	5
1095	Personale	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-interventi-personale	1094	710	711	2	5
1096	Prestazioni di servizi	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-interventi-prestazioni-di-servizi	1094	712	713	2	5
1097	Trasferimenti	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-interventi-trasferimenti	1094	714	715	2	5
1098	Interessi passivi e oneri finanziari diversi	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-interventi-interessi-passivi-e-oneri-finanziari-diversi	1094	716	717	2	5
1099	Altre spese per interventi correnti	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-interventi-altre-spese-per-interventi-correnti	1094	718	719	2	5
1103	Organi istituzionali	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-amministrazione-organi-istituzionali	1102	725	726	2	6
1102	Amministrazione	\N	consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni-amministrazione	1101	724	729	2	5
1155	Amministrazione (altro)	\N	consuntivo-spese-cassa-spese-correnti-funzioni-amministrazione-amministrazione-altro	1153	843	844	2	6
1160	Assistenza, beneficenza e altro	\N	consuntivo-spese-cassa-spese-correnti-funzioni-sociale-assistenza-beneficenza-e-altro	1156	853	854	2	6
827	Contributi e trasferimenti da altri enti pubblici	\N	consuntivo-entrate-cassa-contributi-pubblici-contributi-da-altri-enti-pubblici	824	1523	1524	2	4
802	Vendite e trasferimenti di capitali		consuntivo-entrate-riscossioni-in-conto-residui-vendite-e-trasferimenti-di-capitali	768	1478	1495	2	3
1243	Conferimenti di capitale	\N	consuntivo-spese-cassa-spese-per-investimenti-interventi-conferimenti-di-capitale	1237	1022	1023	2	5
1484	Utilizzo avanzo di amministrazione esercizio precedente	\N	consuntivo-riassuntivo-utilizzo-avanzo-di-amministrazione-esercizio-precedente	1446	117	132	2	2
1490	Spese di investimento	\N	consuntivo-riassuntivo-utilizzo-avanzo-di-amministrazione-esercizio-precedente-spese-di-investimento	1484	130	131	2	3
1491	Estinzione anticipata dei prestiti	\N	consuntivo-riassuntivo-utilizzo-avanzo-di-amministrazione-esercizio-precedente-estinzione-anticipata-dei-prestiti	1484	118	119	2	3
1500	Riaccertamento dei residui	\N	consuntivo-riassuntivo-riaccertamento-dei-residui	1446	97	104	2	2
1502	Eventuale disavanzo da riaccertamento dei residui di cui di parte corrente	\N	consuntivo-riassuntivo-riaccertamento-dei-residui-eventuale-disavanzo-da-riaccertamento-dei-residui-di-cui-di-parte-corrente	1500	102	103	2	3
1503	Eventuale disavanzo da riaccertamento dei residui di cui di parte capitale	\N	consuntivo-riassuntivo-riaccertamento-dei-residui-eventuale-disavanzo-da-riaccertamento-dei-residui-di-cui-di-parte-capitale	1500	100	101	2	3
1510	Esecuzione forzata	\N	consuntivo-riassuntivo-esecuzione-forzata	1446	15	18	2	2
1511	Procedimenti di esecuzione forzata	\N	consuntivo-riassuntivo-esecuzione-forzata-procedimenti-di-esecuzione-forzata	1510	16	17	2	3
\.


--
-- Name: bilanci_voce_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('bilanci_voce_id_seq', 1511, true);


--
-- PostgreSQL database dump complete
--

