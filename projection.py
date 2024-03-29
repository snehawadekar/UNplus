import sys
try:
	import psycopg2
except ImportError:
	pass

sys.path.append('../')

import reveal_globals
import datetime
import csv
import copy
import math
import executable


def is_number(s):
	try:
		float(s)
		return True
	except ValueError:
		return False

def is_int(s):
	try:
		int(s)
		return True
	except ValueError:
		return False


def getProjectedAttributes():
    # reveal_globals.global_filter_predicates = reveal_globals.global_proj # donot include this line for UN1
    print("inside -- projection.getProjectedAttributes")
    attrib_types_dict = {}
    for entry in reveal_globals.global_attrib_types:
        attrib_types_dict[(entry[0], entry[1])] = entry[2]
    #Truncate all core relations
    for table in reveal_globals.global_core_relations:
        cur = reveal_globals.global_conn.cursor()
        cur.execute('Truncate Table ' + table + ';')
        cur.close()
    projectedAttrib = []
    projectedAttrib1 = []
    projection_names = []
    value_used = []
    #Identifying projected attributs with no filter
    dummy_int = 2
    dummy_char = 65 # to avoid having space/tab
    dummy_date = datetime.date(1000,1,1)
    dummy_varbit = format(0, "b")
    dummy_boolean = True
    for entry in reveal_globals.global_filter_predicates:
        value_used.append(entry[1])
        if 'char' in attrib_types_dict[(entry[0],entry[1])] or 'text' in attrib_types_dict[(entry[0], entry[1])]:
            value_used.append(entry[3].replace('%', ''))
        else:
            # if entry[2] == '>=':
            #     value_used.append(entry[3])
            # elif entry[2] == '<=':
            #     value_used.append(entry[4])
            # else:
            value_used.append(entry[3])
                
    for elt in reveal_globals.global_join_graph:
        while dummy_int in value_used:
            dummy_int = dummy_int + 1
        for val in elt:
            value_used.append(val)
            value_used.append(dummy_int)
    for i in range(len(reveal_globals.global_core_relations)):
        tabname = reveal_globals.global_core_relations[i]
        attrib_list = reveal_globals.global_all_attribs[i]
        insert_values = []
        att_order='('
        for attrib in attrib_list:
            att_order=att_order+attrib+","
            if attrib in value_used and ('int' in attrib_types_dict[(tabname, attrib)] or 'numeric' in attrib_types_dict[(tabname, attrib)]):
                insert_values.append(value_used[value_used.index(attrib) + 1])
            elif attrib in value_used and 'date' in attrib_types_dict[(tabname, attrib)]:
                insert_values.append("'" + str(value_used[value_used.index(attrib) + 1]) + "'")
            elif attrib in value_used:
                insert_values.append(str(value_used[value_used.index(attrib) + 1]))
            elif 'int' in attrib_types_dict[(tabname, attrib)] or 'numeric' in attrib_types_dict[(tabname, attrib)]:
                while dummy_int in value_used:
                    dummy_int = dummy_int + 1
                insert_values.append(dummy_int)
                value_used.append(attrib)
                value_used.append(dummy_int)
            elif 'date' in attrib_types_dict[(tabname, attrib)]:
                while dummy_date in value_used:
                    dummy_date = dummy_date + datetime.timedelta(days=1)
                value_used.append(attrib)
                insert_values.append("'" + str(dummy_date) + "'")
                value_used.append(dummy_date)
            elif 'boolean' in attrib_types_dict[(tabname, attrib)]:
                value_used.append(attrib)
                insert_values.append(dummy_boolean)
                value_used.append(str(dummy_boolean))
            else:
                while chr(dummy_char) in value_used:
                    dummy_char = dummy_char + 1
                insert_values.append(chr(dummy_char))
                value_used.append(attrib)
                value_used.append(chr(dummy_char))
        insert_values = tuple(insert_values)
        esc_string = '(' + '%s'
        for j in range(1, len(attrib_list)):
            esc_string = esc_string + ", " + '%s'
        esc_string = esc_string + ")"
        att_order=att_order[:-1]
        att_order+=')'
        cur = reveal_globals.global_conn.cursor()
        print("INSERT INTO " + tabname + att_order + " VALUES " + esc_string, insert_values)
        cur.execute("INSERT INTO " + tabname + att_order + " VALUES " + esc_string, insert_values)
        #conn.commit()
        cur.close()
    value_used = [str(val) for val in value_used]
    new_result = executable.getExecOutput()
    projection_names = list(new_result[0])
    if len(new_result) <= 1:
        reveal_globals.error="Unmasque:\n some error in generating new database. Result is empty. Can not identify projections"
        print('some error in generating new database. Result is empty. Can not identify projections')
        return 0
        # exit(1)
    #Analyze values of this new result
    new_result = list(new_result[1])
    new_result = [x.strip() for x in new_result]
    for val in new_result:
    	#check for value being decimal
        if is_number(val):
            new_val = str(int(float(val)))
        else:
            new_val = val
        if new_val in value_used and not (any(value_used[value_used.index(new_val) - 1] in i for i in reveal_globals.global_filter_predicates)):
            projectedAttrib1.append(value_used[value_used.index(new_val) - 1])
        else:
            projectedAttrib1.append('')

    # print("projectedAttrib org  :",projectedAttrib)
    # # aug 5
    for val in new_result:
        val2=val
        if is_number(val):
            if val2.isdigit():
                new_val = str(int(float(val)))
                if new_val in value_used and not(any(value_used[value_used.index(new_val) - 1] in i for i in reveal_globals.global_filter_predicates)):
                    projectedAttrib.append(value_used[value_used.index(new_val) - 1])
                else:
                    projectedAttrib.append('')


            # elif val2.replace('.','',1).isdigit() :
            else:
                # print("float(val)-int(val)	:",float(val)-int(val))
                new_val=str(float(val))
                if new_val in value_used and (any(value_used[value_used.index(new_val) - 1] in i for i in reveal_globals.global_filter_predicates)):
                    projectedAttrib.append(value_used[value_used.index(new_val) - 1])
                else:
                    projectedAttrib.append('')
        else:
            new_val = val
            if new_val in value_used and not(any(value_used[value_used.index(new_val) - 1] in i for i in reveal_globals.global_filter_predicates)):
                projectedAttrib.append(value_used[value_used.index(new_val) - 1])
            else:
                projectedAttrib.append('')
    
    # print("projectedAttrib after change  :",projectedAttrib)
    # print("projectionnames  :",    projection_names)

    for i in range(0,len(projectedAttrib)):
        if projectedAttrib[i]=='' and projectedAttrib1[i]!='':
            projectedAttrib[i]=projectedAttrib1[i]
    #aug5
        
    #Identifying Projected Attributes with filter
    if '' in projectedAttrib:
        newfilterList = copy.deepcopy(reveal_globals.global_filter_predicates)
        while '' in projectedAttrib and len(newfilterList) != 0:
            dummy_int = 2
            dummy_char = 65 # to avoid having space/tab
            dummy_date = datetime.date(1000,1,1)
            #Truncate all core relations
            for table in reveal_globals.global_core_relations:
                cur = reveal_globals.global_conn.cursor()
                cur.execute('Truncate Table ' + table + ';')
                ##conn.commit()
                cur.close()
            curr_attrib = [newfilterList[0]]
            index = 1
            while(index < len(newfilterList) and curr_attrib[0][2] != '=' and curr_attrib[0][2] != 'equal'):
                curr_attrib[0] = newfilterList[index]
                index = index + 1
            if 'char' in attrib_types_dict[(curr_attrib[0][0], curr_attrib[0][1])] or 'text' in attrib_types_dict[(curr_attrib[0][0], curr_attrib[0][1])]:
                if '_' in curr_attrib[0][3]:
                    curr_value = curr_attrib[0][3].replace('_', chr(dummy_char))
                    dummy_char = dummy_char + 1
                else:
                    curr_value = curr_attrib[0][3].replace('%', chr(dummy_char), 1)
                    dummy_char = dummy_char + 1
                curr_value = curr_value.replace('%', '')
            elif 'date' in attrib_types_dict[(curr_attrib[0][0], curr_attrib[0][1])]:
                curr_value = curr_attrib[0][3]
            elif 'numeric' in attrib_types_dict[(curr_attrib[0][0], curr_attrib[0][1])]:
                curr_value = curr_attrib[0][3]
            else:
                curr_value = int(curr_attrib[0][3])
            value_used = [curr_attrib[0][1], curr_value]
            for entry in reveal_globals.global_filter_predicates:
                if entry != curr_attrib[0] and ('int' in attrib_types_dict[(entry[0], entry[1])] or 'numeric' in attrib_types_dict[(entry[0], entry[1])]):
                    #indicates integer type attribute
                    value_used.append(entry[1])
                    value_used.append(0)
                    for i in range(int(entry[3]), int(entry[4]) + 1):
                        value_used[-1] = i
                        if i != curr_value:
                            break
                    if value_used[-1] == curr_value:
                        curr_attrib.append(entry)
                elif entry != curr_attrib[0] and 'date' in attrib_types_dict[(entry[0], entry[1])]:
                    value_used.append(entry[1])
                    value_used.append(entry[3])
                    for i in range(int((entry[4] - entry[3]).days)):
                        value_used[-1] = entry[3] + datetime.timedelta(days=i)
                        if value_used[-1] != curr_value:
                            break
                        if value_used[-1] == curr_value:
                            curr_attrib.append(entry)
                elif entry != curr_attrib[0] and ('char' in attrib_types_dict[(entry[0], entry[1])] or 'text' in attrib_types_dict[(entry[0], entry[1])]):
                    #character type attribute
                    value_used.append(entry[1])
                    curr_str = entry[3]
                    value_used.append(curr_str)
                    while '_' in curr_str or '%' in curr_str:
                        if '_' in curr_str:
                            curr_str = curr_str.replace('_', chr(dummy_char))
                        else:
                            curr_str = curr_str.replace('%', chr(dummy_char), 1)
                        curr_str = curr_str.replace('%', '')
                        dummy_char = dummy_char + 1
                        if curr_str != curr_value:
                            value_used[-1]
                            break
                        curr_str = entry[3]
                    if value_used[-1] == curr_value:
                        curr_attrib.append(entry)
            for elt in reveal_globals.global_join_graph:
                while dummy_int in value_used:
                    dummy_int = dummy_int + 1
                for val in elt:
                    value_used.append(val)
                    value_used.append(dummy_int)
            for i in range(len(reveal_globals.global_core_relations)):
                tabname = reveal_globals.global_core_relations[i]
                attrib_list = reveal_globals.global_all_attribs[i]
                insert_values = []
                att_order = '('
                for attrib in attrib_list:
                    att_order = att_order + attrib +","
                    if attrib in value_used and ('int' in attrib_types_dict[(tabname, attrib)] or 'numeric' in attrib_types_dict[(tabname, attrib)]):
                        insert_values.append(value_used[value_used.index(attrib) + 1])
                    elif attrib in value_used and 'date' in attrib_types_dict[(tabname, attrib)]:
                        insert_values.append("'" + str(value_used[value_used.index(attrib) + 1]) + "'")
                    elif attrib in value_used:
                        insert_values.append(str(value_used[value_used.index(attrib) + 1]))
                    elif 'int' in attrib_types_dict[(tabname, attrib)] or 'numeric' in attrib_types_dict[(tabname, attrib)]:
                        while dummy_int in value_used:
                            dummy_int = dummy_int + 1
                        insert_values.append(dummy_int)
                        value_used.append(attrib)
                        value_used.append(dummy_int)
                    elif 'date' in attrib_types_dict[(tabname, attrib)]:
                        while dummy_date in value_used:
                            dummy_date = dummy_date + datetime.timedelta(days=1)
                        value_used.append(attrib)
                        insert_values.append("'" + str(dummy_date) + "'")
                        value_used.append(dummy_date)
                    elif 'bit varying' in attrib_types_dict[(tabname, attrib)]:
                        value_used.append(attrib)
                        insert_values.append(dummy_varbit)
                        value_used.append(str(dummy_varbit))
                    elif 'boolean' in attrib_types_dict[(tabname, attrib)]:
                        value_used.append(attrib)
                        insert_values.append(dummy_boolean)
                        value_used.append(str(dummy_boolean))
                    else:
                        while(chr(dummy_char) in value_used):
                            dummy_char = dummy_char + 1
                        insert_values.append(chr(dummy_char))
                        value_used.append(attrib)
                        value_used.append(chr(dummy_char))
                insert_values = tuple(insert_values)
                esc_string = '(' + '%s'
                for j in range(1, len(attrib_list)):
                    esc_string = esc_string + ", " + '%s'
                esc_string = esc_string + ")"
                cur = reveal_globals.global_conn.cursor()
                att_order=att_order[:-1]
                att_order+=')'
                cur.execute("INSERT INTO " + tabname + att_order + " VALUES " + esc_string, insert_values)
                #conn.commit()
                cur.close()
            value_used = [str(val) for val in value_used]
            new_result = executable.getExecOutput()
            if len(new_result) <= 1:
                reveal_globals.error="Unmasque: \n some error in generating new database. Result is empty. Can not identify projections completely."
                print('some error in generating new database. Result is empty. Can not identify projections completely.')
                return 0
                # exit(1)
            #Analyze values of this new result
            new_result = list(new_result[1])
            new_result = [x.strip() for x in new_result]
            for i in range(len(new_result)):
                #check for value being decimal
                if is_number(new_result[i]):
                    new_result[i] = str(int(float(new_result[i])))
            for i in range(len(new_result)):
                if projectedAttrib[i] == '' and str(new_result[i]) == str(curr_value).strip():
                    projectedAttrib[i] = curr_attrib[0][1]
                    if len(curr_attrib) > 1:
                        newfilterList.remove(curr_attrib[0])
                        del(curr_attrib[0])
            for val in curr_attrib:
                newfilterList.remove(val)
            curr_attrib = []
    #HARDCODING FOR PROJECTION FOR NOW
    reveal_globals.local_other_info_dict = {}
    reveal_globals.local_other_info_dict['Current Mutation'] = 'No Mutation'
    reveal_globals.local_other_info_dict[u'Candidate List \u2014 revenue'] = "[l_extendedprice]"
    reveal_globals.local_other_info_dict[u'Candidate List \u2014 o_orderdate'] = "[o_orderdate]"
    reveal_globals.local_other_info_dict[u'Candidate List \u2014 o_shippriority'] = "[o_shippriority]"
    reveal_globals.local_other_info_dict[u'Candidate List \u2014 l_orderkey'] = "[l_orderkey, o_orderkey]"
    reveal_globals.local_other_info_dict['Conclusion'] = 'No Pruning Required'
    reveal_globals.global_other_info_dict['projection_D_mut1'] = copy.deepcopy(reveal_globals.local_other_info_dict)
    #HARDCODIG FOR DEMO (TO BE REMOVED)
    for i in range(len(projectedAttrib)):
        if projectedAttrib[i].strip() == 'o_orderkey':
            projectedAttrib[i] = 'l_orderkey'
    #####################################
    return projectedAttrib, projection_names