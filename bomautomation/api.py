from __future__ import unicode_literals
import frappe, erpnext, math, json
from frappe import _
import traceback
import json
import ast
from datetime import datetime


@frappe.whitelist()
def app_error_log(title,error):
	d = frappe.get_doc({
			"doctype": "Custom Error Log",
			"title":str("User:")+str(title),
			"error":traceback.format_exc()
		})
	d = d.insert(ignore_permissions=True)
	return d


@frappe.whitelist()
def make_bom(name,selected_items,selected_bom):
	try:
		so_doc=frappe.get_doc("Sales Order",name)
		if len(so_doc.items)>=1:
			if len(so_doc.row_materials)>=1:				
				for item in so_doc.items:
					if item.name in selected_items:
						res=validate_avaialable_bom(name,item.name)
						if not res==False:
							bom_doc=frappe.get_doc("BOM",res)
							idx=len(bom_doc.items)+1
							for row in so_doc.row_materials:
								if row.name in selected_bom:
									count=0
									for bom_item in bom_doc.items:
										if bom_item.item_code==row.item_code:
											count += 1
									if count==0:
										add_bom_item(row.item_code,row.item_name,row.uom,(row.qty*item.qty+(row.qty*item.qty*(row.wastage_ratio/100))),row.operation,row.notes,res,idx)
										idx += 1
									
							bom_doc_final=frappe.get_doc("BOM",res)
							bom_doc_final.save()
							msg='BOM '+'<a href="#Form/BOM/'+bom_doc_final.name+'">'+bom_doc_final.name+'</a>'+' Updated'
							frappe.msgprint(msg);
						
						else:
							row_materials=[]
							for row in so_doc.row_materials:
								if row.name in selected_bom:
									row_dict={}
									row_dict["item_code"]=row.item_code
									row_dict["item_name"]=row.item_name
									row_dict["item_name"]=row.item_name
									row_dict["operation"]=row.operation
									row_dict["note"]=row.notes
									row_dict["weight_per_unit"]=row.weight_per_unit
									row_dict["qty"]=(row.qty*item.qty+(row.qty*item.qty*(row.wastage_ratio/100)))
									row_materials.append(row_dict)
							create_bom(item.item_code,row_materials,so_doc.company,"USD",item.qty,so_doc.name,so_doc.po_no,so_doc.routing)
			else:
				frappe.throw("Row Materials Required For Generate BOM")
		else:
			frappe.throw("Items Required For Generate BOM")

	except Exception as e:
		error_log=app_error_log(frappe.session.user,str(e))

def validate_avaialable_bom(so_no,si_no):
	so_item=frappe.get_doc("Sales Order Item",si_no)
	bom_details=frappe.db.sql("""select name from `tabBOM` 
		where sales_order=%s and item=%s and docstatus=0 limit 1"""
		,(so_no,so_item.item_code),as_dict=1)
	if len(bom_details)>=1:
		return bom_details[0].name
	else:
		return False
		

def create_bom(item,item_details,company,currency,qty,sales_order,po,routing):
	try:
		bom_doc=frappe.get_doc(dict(
			doctype="BOM",
			company=company,
			currency=currency,
			item=item,
			items=item_details,
			quantity=qty,
			rm_cost_as_per="Valuation Rate",
			sales_order=sales_order,
			customer_purchase_order=po,
			routing=routing
		)).insert()
		msg='BOM '+'<a href="#Form/BOM/'+bom_doc.name+'">'+bom_doc.name+'</a>'+' Created'
		frappe.msgprint(msg);

	except Exception as e:
		frappe.errprint(json.dumps(item_details))
		error_log=app_error_log(frappe.session.user,str(e))

def add_bom_item(item_code,item_name,uom,qty,operation,notes,name,idx):
	doc=frappe.get_doc(dict(
		doctype="BOM Item",
		parent=name,
		parenttype="BOM",
		parentfield="items",
		item_code=item_code,
		item_name=item_name,
		uom=uom,
		qty=qty,
		rate=0,
		note=notes,
		operation=operation,
		idx=idx
	)).insert()


@frappe.whitelist()
def make_match_bom(name,selected_items,selected_bom,match_length):
	try:
		so_doc=frappe.get_doc("Sales Order",name)
		if len(so_doc.items)>=1:
			if len(so_doc.row_materials)>=1:				
				for item in so_doc.items:
						char=item.item_code;
						match_lin=int(match_length);
						x=match_lin;
						match_char=char[-x:];
						res=validate_avaialable_bom(name,item.name)
						if not res==False:
							bom_doc=frappe.get_doc("BOM",res)
							idx=len(bom_doc.items)+1
							for row in so_doc.row_materials:
								if row.item_code[-x:] == match_char:
									count=0
									for bom_item in bom_doc.items:
										if bom_item.item_code==row.item_code:
											count += 1
									if count==0:
										add_bom_item(row.item_code,row.item_name,row.uom,(row.qty*item.qty+(row.qty*item.qty*(row.wastage_ratio/100))),row.operation,row.notes,res,idx)
										idx += 1
									
							bom_doc_final=frappe.get_doc("BOM",res)
							bom_doc_final.save()
							msg='BOM '+'<a href="#Form/BOM/'+bom_doc_final.name+'">'+bom_doc_final.name+'</a>'+' Updated'
							frappe.msgprint(msg);
						
						else:
							row_materials=[]
							for row in so_doc.row_materials:
								if row.item_code[-x:] == match_char:
									row_dict={}
									row_dict["item_code"]=row.item_code
									row_dict["item_name"]=row.item_name
									row_dict["item_name"]=row.item_name
									row_dict["note"]=row.notes
									row_dict["weight_per_unit"]=row.weight_per_unit
									row_dict["operation"]=row.operation
									row_dict["qty"]=(row.qty*item.qty+(row.qty*item.qty*(row.wastage_ratio/100)))
									row_materials.append(row_dict)
							create_bom(item.item_code,row_materials,so_doc.company,"USD",item.qty,so_doc.name,so_doc.po_no,so_doc.routing)
			else:
				frappe.throw("Row Materials Required For Generate BOM")
		else:
			frappe.throw("Items Required For Generate BOM")

	except Exception as e:
		error_log=app_error_log(frappe.session.user,str(e))

@frappe.whitelist()		
def add_StockEntry_from_JobCard(name,myWorkOrder,mFollowUp,qty,myBom,mYitem,mYoperation):
	try:
		#fruit='[{"item_code": "Pocketing/MTR-BLENDED-DHE/S21-OFF WHITE-80%PES 20%CO-PIGMENT COATING-PLAIN-147CM" ,"qty": 9.792 ,"umo": "Meter" ,"s_warehouse": "pockting warehouse - GFFRM" ,"t_warehouse": "Work In Progress - GFFRM" },{"item_code": "Pocketing/MTR-BLENDED-DHE/S21-OFF WHITE-80%PES 20%CO-PIGMENT COATING-PLAIN-147CM" ,"qty": 9.792 ,"umo": "Meter" ,"s_warehouse": "pockting warehouse - GFFRM" ,"t_warehouse": "Work In Progress - GFFRM" }]'
		#,'{"item_code": "Pocketing/MTR-BLENDED-DHE/S21-OFF WHITE-80%PES 20%CO-PIGMENT COATING-PLAIN-147CM" ,"qty": 9.792 ,"umo": "Meter" ,"s_warehouse": "pockting warehouse - GFFRM" ,"t_warehouse": "Work In Progress - GFFRM" }]'#,'{"item_code": "Fabric-BLENDED-RACE(DHE)-PFD-98%CO 2A-DUBBY-160CM" ,"qty": 32.64 ,"umo": "Meter" ,"s_warehouse": "FABRIC WAREHOUSE - GFFRM" ,"t_warehouse": "Work In Progress - GFFRM" }'		#, '{"item_code": "FUSING-BARLON-WHITE -WOVEN-STREATCH-150CM-100%POLYESTER" ,"qty": 4 ,"umo": "Meter" ,"s_warehouse": "FUSING WARHOUSE - GFFRM" ,"t_warehouse": "Work In Progress - GFFRM" }' , '{"item_code": "FUSING-4489-WHITE -NON WOVEN-POLYESTER-90CM" ,"qty": 2 ,"umo": "Meter" ,"s_warehouse": "FUSING WARHOUSE - GFFRM" ,"t_warehouse": "Work In Progress - GFFRM" }
		#fruit= ['{"foo":"bar", "foo2":"bar2"}','{"foo2":"bar2", "foo23":"bar23"}']
		#fruit= '[{"foo":"bar", "foo2":"bar2"},{"foo2":"ba2r", "fo2o2":"b2ar2"},{"foo2":"ba2r", "fo2o2":"b2ar2"}]'
		#fruit='[{"item_code": "Pocketing/MTR-BLENDED-DHE/S21-OFF WHITE-80%PES 20%CO-PIGMENT COATING-PLAIN-147CM" ,"qty": 9.792 ,"umo": "Meter" ,"s_warehouse": "pockting warehouse - GFFRM" ,"t_warehouse": "Work In Progress - GFFRM" },{"item_code": "Pocketing/MTR-BLENDED-DHE/S21-OFF WHITE-80%PES 20%CO-PIGMENT COATING-PLAIN-147CM" ,"qty": 9.792 ,"umo": "Meter" ,"s_warehouse": "pockting warehouse - GFFRM" ,"t_warehouse": "Work In Progress - GFFRM" }]'
		#fruit='[{"item_code": "Pocketing/MTR-BLENDED-DHE/S21-OFF WHITE-80%PES 20%CO-PIGMENT COATING-PLAIN-147CM" ,"qty": 18.1152 ,"umo": "Meter" ,"s_warehouse": "pockting warehouse - GFFRM" ,"t_warehouse": "Work In Progress - GFFRM" } , {"item_code": "Fabric-BLENDED-RACE(DHE)-PFD-98%CO 2%EA-DUBBY-160CM" ,"qty": 60.384 ,"umo": "Meter" ,"s_warehouse": "FABRIC WAREHOUSE - GFFRM" ,"t_warehouse": "Work In Progress - GFFRM" } , {"item_code": "FUSING-BARLON-WHITE -WOVEN-STREATCH-150CM-100%POLYESTER" ,"qty": 7.4 ,"umo": "Meter" ,"s_warehouse": "FUSING WARHOUSE - GFFRM" ,"t_warehouse": "Work In Progress - GFFRM" } , {"item_code": "FUSING-4489-WHITE -NON WOVEN-POLYESTER-90CM" ,"qty": 3.7 ,"umo": "Meter" ,"s_warehouse": "FUSING WARHOUSE - GFFRM" ,"t_warehouse": "Work In Progress - GFFRM" } ]'
		#fruit='[{"item_code": "Pocketing/MTR-BLENDED-DHE/S21-OFF WHITE-80%PES 20%CO-PIGMENT COATING-PLAIN-147CM" ,"qty": 18.1152 ,"umo": "Meter" ,"s_warehouse": "pockting warehouse - GFFRM" ,"t_warehouse": "Work In Progress - GFFRM" } , {"item_code": "Fabric-BLENDED-RACE(DHE)-PFD-98%CO 2%EA-DUBBY-160CM" ,"qty": 60.384 ,"umo": "Meter" ,"s_warehouse": "FABRIC WAREHOUSE - GFFRM" ,"t_warehouse": "Work In Progress - GFFRM" } , {"item_code": "FUSING-BARLON-WHITE -WOVEN-STREATCH-150CM-100%POLYESTER" ,"qty": 7.4 ,"umo": "Meter" ,"s_warehouse": "FUSING WARHOUSE - GFFRM" ,"t_warehouse": "Work In Progress - GFFRM" } , {"item_code": "FUSING-4489-WHITE -NON WOVEN-POLYESTER-90CM" ,"qty": 3.7 ,"umo": "Meter" ,"s_warehouse": "FUSING WARHOUSE - GFFRM" ,"t_warehouse": "Work In Progress - GFFRM" } ]'
		mYitem='['+ mYitem +']'
		fruit = json.loads(mYitem)
		#Dict = eval(fruit)
		#ast.literal_eval(fruit)
		#msg=fruit.item_code
		#mYitem.replace("'", '"')
		#frappe.msgprint(mYitem);
		#myItemss=json.loads(myItems)
		# arryItem = yaml.load(myItems)
		#frappe.errprint(arryItem)
		bom_doc=frappe.get_doc(dict(
			doctype="Stock Entry",
			stock_entry_type='Material Transfer for Manufacture',
			work_order=myWorkOrder,
			follow_up_no=mFollowUp,
			bom_no=myBom,
			operation=mYoperation,
			from_bom=1,
			fg_completed_qty=qty,
			job_card=name,
			items= fruit
		)).insert()
		msg='Stock Entry '+'<a href="#Form/Stock Entry/'+bom_doc.name+'">'+bom_doc.name+'</a>'+' Created'
		frappe.msgprint(msg);
		#@frappe.msgprint(msg);
	except Exception as e:
		error_log=app_error_log(frappe.session.user,str(e))

@frappe.whitelist()		
def update_submit_jobcard(name,qty,fromTime,toTime):
	
	doc = frappe.get_doc("Job Card",name)
	row = doc.append("time_logs", {})
	row.from_time = fromTime
	row.to_time = toTime
	row.completed_qty = float(qty)
	doc.save()
	doc.submit()
	frappe.msgprint('Job Card updated and submitted  ');
	