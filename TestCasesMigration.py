import time
import linecache
import sys

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)


#define column mapping
ID_COL = 0
AUTOMATED = 1
PROJECT = 2
NAME = 3
GOAL = 4
PRECONDITIONS = 5
ESTIMATEDEXECTIME = 6
STEP = 7
ER = 8
STEPNOTES = 9



def write_header_col(ws):
    ws.write(0,ID_COL, 'ID')
    ws.write(0,AUTOMATED, 'Automated')
    ws.write(0,PROJECT, 'Project')   
    ws.write(0,NAME, 'Name') 
    ws.write(0,GOAL, 'Goal')
    ws.write(0,PRECONDITIONS, 'Pre-Conditions')    
    ws.write(0,ESTIMATEDEXECTIME, 'Estimated Execution Time')
    ws.write(0,STEP, 'Step')
    ws.write(0,ER, 'Expected Result')
    ws.write(0,STEPNOTES, 'Step Notes')     
    

#for first level testlink-exports that are nested
def parse_nested_xml(test_link_export_file):
    project_code = "VoiceArtisan_Client" #this will be used as the ID field in Contour

    #teams appear to be using different keywords for automated and automation candidate tests...specify what your team uses here
    automated_keyword = "Automated"
    automation_candidate_keyword = "AutomationCandidate"

    # DOC for ElementTree - https://docs.python.org/2/library/xml.etree.elementtree.html
    import xml.etree.ElementTree as ET
    import xlwt
    tree = ET.parse('./Input_XML_Folder/' + test_link_export_file)
    root = tree.getroot()

    top_level_suite_name = root.attrib.get('name')
    top_level_suite_name = top_level_suite_name.replace(" ", "")

    #create a new excel workbook
    wb = xlwt.Workbook()
    #add a sheet to the workbook named the same name as our top_level_test_suite
    ws = wb.add_sheet(top_level_suite_name, cell_overwrite_ok=True)
    #write the header column
    write_header_col(ws)
    row = 1
    test_id = 0
    
    #do some work
    for element in root:    
        #test suite name
        test_suite_name = element.attrib.get('name')
        print "Testsuite:", test_suite_name
        if test_suite_name != None:
            ws.write(row,ID_COL, project_code + "-")
            ws.write(row,PROJECT, 'Vocollect')  
            style = xlwt.easyxf('pattern: pattern solid, fore_colour red')
            ws.write(row,NAME, test_suite_name, style) 
            row +=1
            for child in element:
                #while (retry <5):
                if child.__len__() > 0:
                    if child.tag == 'testsuite':
                        print "Nested Testsuite:",child.attrib.get('name')
                        element = child
                        test_suite_name = "Nested Test Suite Under :"+"===>>"+test_suite_name+"===>>"+element.attrib.get('name')
                        if test_suite_name != None:
                            ws.write(row,ID_COL, project_code + "-")
                            ws.write(row,PROJECT, 'Vocollect')  
                            style = xlwt.easyxf('pattern: pattern solid, fore_colour red')
                            ws.write(row,NAME, test_suite_name, style) 
                            row +=1 ####
                            for child in element:
                                if child.__len__() > 0:
                                    if child.tag == 'testcase':
                                        row = parse_testcase_nodes(ID_COL,PROJECT,NAME,ws,child,row,test_id,project_code,automated_keyword,automation_candidate_keyword,"NestedTestCase")
                    elif child.tag == 'testcase':
                        row = parse_testcase_nodes(ID_COL,PROJECT,NAME,ws,child,row,test_id,project_code,automated_keyword,automation_candidate_keyword,"TestCase")
    try:
        #wb.Settings.CheckExcelRestriction
        wb.save('./Output_XLS_Folder/' + top_level_suite_name + '.xlsm')
        print "\n\nScript complete.  Excel file created successfully."
    except Exception, e:
        print "exception occured:",e
        PrintException()



def parse_testcase_nodes(ID_COL,PROJECT,NAME,ws,child,row,test_id,project_code,automated_keyword,automation_candidate_keyword,parent):
    print "{0}:".format(parent),child.attrib.get('name')
    test_id += 1
    #we found a test case start writing to the next row 
    testcase_name = child.attrib.get('name')
    ws.write(row,ID_COL, project_code + "-")
    ws.write(row,PROJECT, 'Vocollect')  
    ws.write(row,NAME, testcase_name) 
    
    #KEYWORDS
    keywords = child.find('keywords')
    if keywords != None:
        for keyword in keywords:
            keyword = keyword.attrib.get('name')
            if keyword == automated_keyword:
                ws.write(row,AUTOMATED, 'Yes')
            elif keyword == automation_candidate_keyword:
                ws.write(row,AUTOMATED, 'Planned')
            
    
    #ESTIMATED EXEC. TIME
    customfields = child.find('custom_fields')
    if customfields != None:
        for customfield in customfields:
            man_exec_time = customfield.find('value').text
            if man_exec_time != None:
                ws.write(row,ESTIMATEDEXECTIME, man_exec_time)
                
                
    #PRE-CONDITIONS
    testcase = child.getchildren()
    pc = child.find('preconditions')
    if len(str(pc.text<32767)):
        ws.write(row,PRECONDITIONS, pc.text)
    else:
        alert = ' has non-standard text, a long summary, or additional styling.  It is recommened that you manually check this field after import to ensure all text has been captured successfully.\n\n'
        print testcase_name.upper() + alert
        ws.write(row, PRECONDITIONS, 'CONFIRM MIGRATION: {0} This field'.format(testcase_name.upper()) + alert + pc.text[0:32000])
    
    
    
    #GOAL/SUMMARY
    testcase = child.getchildren()
    summary = child.find('summary')
    
    # the excel module can only write up to 32767 bytes, if a summary is a longer, alert the user that this test case
    # will need to be migrated manually.
    if summary.text != None:
        if len(summary.text) < 32767:
            ws.write(row, GOAL, summary.text)
        else:
            alert = ' has non-standard text, a long summary, or additional styling.  It is recommened that you manually check this field after import to ensure all text has been captured successfully.\n\n'
            print testcase_name.upper() + alert
            ws.write(row, GOAL, 'CONFIRM MIGRATION: This field' + alert + summary.text[0:32000])
            ws.write(row,NAME, 'CONFIRM MIGRATION: '+ testcase_name)

    
   #steps
    steps = child.find('steps')
    stepnum = 1
    if steps != None:
        for step in steps:
            astep = step.find('actions')
            if stepnum > 1:
                #if there are more the 1 step, re-write the other info.
                ws.write(row,ID_COL, project_code + "-")
                ws.write(row,PROJECT, 'Vocollect')
                ws.write(row,NAME, testcase_name) 
            #write steps stuff
            if len(str(astep.text<32767)):
                ws.write(row,STEP, astep.text)
            else:
                alert = ' has non-standard text, a long summary, or additional styling.  It is recommened that you manually check this field after import to ensure all text has been captured successfully.\n\n'
                print testcase_name.upper() + alert
                ws.write(row, STEP, 'CONFIRM MIGRATION: {0} This field'.format(testcase_name.upper()) + alert + astep.text[0:32000])                                                    
            stepnum += 1
            #ERS
            ers = step.find('expectedresults')
            if ers.text != None:
                if "style" in ers.text:
                    alert = ' has styling in is ERs that will likely cause import issues.  You must manually capture this ER\n\n'
                    print testcase_name.upper() + alert
                    ws.write(row, ER, 'MIGRATION ALERT:  This ER had styling issues that would have prevented a successful import.  You must manually capture this ER')
                    ws.write(row,NAME, 'CONFIRM MIGRATION: '+ testcase_name)
                else:
                    if len(str(ers.text<32767)):
                        ws.write(row, ER, ers.text)
                    else:
                        alert = ' has non-standard text, a long summary, or additional styling.  It is recommened that you manually check this field after import to ensure all text has been captured successfully.\n\n'
                        print testcase_name.upper() + alert
                        ws.write(row, STEP, 'CONFIRM MIGRATION: {0} This field'.format(testcase_name.upper()) + alert + ers.text[0:32000])
                        
            row += 1
    return row



if __name__ == "__main__":
     if len(sys.argv) > 1:
        test_link_export_file = sys.argv[1]
     else:
        test_link_export_file = 'Part1EncryptDecrypt13.xml' #the test link export file we will be parsing
        #test_link_export_file = 'Vcat_Coexistence_all.xml'
     parse_nested_xml(test_link_export_file)
