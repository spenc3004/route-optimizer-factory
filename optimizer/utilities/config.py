PERMISSIONS = {
    "roi_analysis": ["admin", "sales admin"],
}

PRIVILEGED_USERS = ["admin", "sales admin"]

CATEGORY_CONFIG = {
    "Home Services": {
        "features": {
            "use_wps": True,
            "use_cpms": True,
            "use_vds": False,
            "profile_modes": ["Dynamic (from file)", "Fixed Standard"]
        },
        "currency_columns": ["$ Income", "$ Home Value", "$ Total Spend", "$ Average Order"],
        "percentage_columns": [],
        "numeric_columns": [
            "Distance",
            "Selected",
            "Available",
            "Potential",
            "SFDU",
            "PO Box Res",
            "Seasonal",
            "Customer Count",
            "Customer Penetration%",
            "House Count",
            "Residence Count",
            "Business Count",
            "House Penetration%",
            "Total Visits",
            "Owner Occupied",
            "Median Year Structure Built",
        ],
        "required_columns_base": [
            '$ Income', '$ Home Value', 'Owner Occupied',
            'Median Year Structure Built', 'Distance'
        ],
        "required_columns_by_preset": {
            "Manual": [],
            "Home SRVCS Acquisition (No History)": [],
            "Home SRVCS Acquisition (With History + Suppression)": [
                'House Count', 'House Penetration%', '$ Total Spend',
                'Total Visits', '$ Average Order', 'Selected'
            ],
            "Home SRVCS Acquisition (With History, No Suppression)": [
                'House Count', 'House Penetration%', '$ Total Spend',
                'Total Visits', '$ Average Order', 'Selected'
            ]
        },
        "fail_filters": [
            { 
                "key" : 'min_income', 
                "label" : 'Min Household Income ($)', 
                "required_column" : '$ Income', 
                "threshold" : 40000, 
                "enabled": True
             },
            {
                "key" : 'max_income', 
                "label" : 'Max Household Income ($)', 
                "required_column" : '$ Income', 
                "threshold" : 250000, 
                "enabled": False   
            },
            {
                "key" : 'max_distance', 
                "label" : 'Max Distance (miles)', 
                "required_column" : 'Distance', 
                "threshold" : 50, 
                "enabled": True   
            },
            {
                "key" : 'min_owner', 
                "label" : 'Min Owner Occupied (%)', 
                "required_column" : 'Owner Occupied', 
                "threshold" : 70, 
                "enabled": True   
            },
            {
                "key" : 'max_penetration', 
                "label" : 'Max Penetration (%)', 
                "required_column" : 'House Penetration%', 
                "threshold" : 11.0, 
                "enabled": True   
            }
        ],
        "presets": {
            "Manual": {},
            "Home SRVCS Acquisition (No History)": {
                '$ Income': 0.25,
                '$ Home Value': 0.15,
                'Owner Occupied': 0.30,
                'Median Year Structure Built': 0.05,
                'House Count': 0.00,
                'House Penetration%': 0.00,
                '$ Total Spend': 0.00,
                'Total Visits': 0.00,
                '$ Average Order': 0.00,
                'Distance': 0.25,
                'Weighted Penetration Score': 0.00,
                'Customer Profile Match Score': 0.00
            },
            "Home SRVCS Acquisition (With History + Suppression)": {
                '$ Income': 0.05,
                '$ Home Value': 0.05,
                'Owner Occupied': 0.15,
                'Median Year Structure Built': 0.03,
                'House Count': 0.10,
                'House Penetration%': 0.05,
                '$ Total Spend': 0.07,
                'Total Visits': 0.03,
                '$ Average Order': 0.05,
                'Distance': 0.07,
                'Weighted Penetration Score': 0.15,
                'Customer Profile Match Score': 0.20
            },
            "Home SRVCS Acquisition (With History, No Suppression)": {
                '$ Income': 0.05,
                '$ Home Value': 0.05,
                'Owner Occupied': 0.10,
                'Median Year Structure Built': 0.02,
                'House Count': 0.13,
                'House Penetration%': 0.13,
                '$ Total Spend': 0.13,
                'Total Visits': 0.07,
                '$ Average Order': 0.10,
                'Distance': 0.07,
                'Weighted Penetration Score': 0.05,
                'Customer Profile Match Score': 0.10
            }
        },
        "fallback_weights": {
            '$ Income': 0.15,
            '$ Home Value': 0.10,
            'Owner Occupied': 0.10,
            'Median Year Structure Built': 0.05,
            'House Count': 0.10,
            'House Penetration%': 0.05,
            '$ Total Spend': 0.10,
            'Total Visits': 0.05,
            '$ Average Order': 0.05,
            'Distance': 0.05,
            'Weighted Penetration Score': 0.10,
            'Customer Profile Match Score': 0.10
        },
        "ideals_columns": {
            "$ Income": "Ideal Income",
            "$ Home Value": "Ideal Home Value",
            "Owner Occupied": "Ideal Owner Occupied",
            "Median Year Structure Built": "Ideal Median Year Built",
            "Distance": "Ideal Distance",
        },
        "drivers": [
            "House Count",
            "House Penetration%",
            "$ Total Spend",
            "Total Visits",
            "$ Average Order"
        ],
        "profile_defaults": {
            "ideal_income": 65000,
            "ideal_home_value": 180000,
            "ideal_owner_occupied": 75,
            "ideal_median_year_built": 1995,
            "ideal_distance": 25
        },
        "export_layout": {
            "ranked_columns_order": [
                "Zip Code", "Geocode", "State", "City", "Distance", "Selected", "Available",
                "Potential", "Postal Rates", "$ Add’l Postage", "SFDU", "$ Income",
                "$ Home Value", "Owner Occupied", "%Renter Occupied", "Median Year Structure Built",
                "House Count", "House Penetration%", "$ Total Spend", "Total Visits",
                "$ Average Order", "Customer Profile Match Score", "Composite Score", "Penetration Flag",
                "Status"
            ],
            "ranked_columns_drop": [
                "Segment Name", "Seasonal", "Customer Count", "Customer Penetration%",
                "Residence", "Residence Count", "Business Count", "Total Visits_Norm",
                "House Count_Norm", "House Penetration%_Norm", "Distance_Norm", "$ Income_Norm",
                "$ Average Order_Norm", "$ Total Spend_Norm", "Owner Occupied_Norm",
                "Median Year Structure Built_Norm", "Weighted Penetration Score",
                "Weighted Penetration Score_Norm"
            ],
            "ranked_header_colors": {
                "Zip Code": "#FFFF54",
                "Geocode": "#FFFF54",
                "State": "#FFFF54",
                "City": "#FFFF54",
                "Distance": "#FFFF54",
                "Selected": "#FFFF54",
                "Available": "#FFFF54",
                "Potential": "#FFFF54",
                "Postal Rates": "#FFFF54",
                "$ Add’l Postage": "#FFFF54",
                "SFDU": "#FFFF54",
                "$ Income": "#F2DCDB",
                "$ Home Value": "#F2DCDB",
                "Owner Occupied": "#F2DCDB",
                "%Renter Occupied": "#F2DCDB",
                "Median Year Structure Built": "#F2DCDB",
                "House Count": "#DAEEF3",
                "House Penetration%": "#DAEEF3",
                "$ Total Spend": "#DAEEF3",
                "Total Visits": "#DAEEF3",
                "$ Average Order": "#DAEEF3",
                "Customer Profile Match Score": "#92D050",
                "Composite Score": "#92D050",
                "Penetration Flag": "#92D050",
                "Status": "#92D050"
            },
            "include_winsor_sheet": False,
            "roi_columns_order": [
                 "Zip Code", "Geocode", "State", "City", "Distance", "Selected", "Available",
                "Potential", "Postal Rates", "$ Add’l Postage", "SFDU", "$ Income",
                "$ Home Value", "Owner Occupied", "%Renter Occupied", "Median Year Structure Built",
                "House Count", "House Penetration%", "$ Total Spend", "Total Visits",
                "$ Average Order", "Customer Profile Match Score", "Composite Score", "Penetration Flag",
                "Status", "Times Mailed To", "Overall Mailing Qty", "Overall RO's", "Overall Responded",
                "Overall Revenue", "Overall Expense", "Most Recent Mailed To", "Response Rate", "Overall ROAS", "Response Rate %"
            ],
            "roi_columns_drop": [
                "Segment Name", "Seasonal", "Customer Count", "Customer Penetration%",
                "Residence", "Residence Count", "Business Count", "Total Visits_Norm",
                "House Count_Norm", "House Penetration%_Norm", "Distance_Norm", "$ Income_Norm",
                "$ Average Order_Norm", "$ Total Spend_Norm", "Owner Occupied_Norm",
                "Median Year Structure Built_Norm", "Weighted Penetration Score",
                "Weighted Penetration Score_Norm"
            ],
            "roi_header_colors": {
                "Zip Code": "#FFFF54",
                "Geocode": "#FFFF54",
                "State": "#FFFF54",
                "City": "#FFFF54",
                "Distance": "#FFFF54",
                "Selected": "#FFFF54",
                "Available": "#FFFF54",
                "Potential": "#FFFF54",
                "Postal Rates": "#FFFF54",
                "$ Add’l Postage": "#FFFF54",
                "SFDU": "#FFFF54",
                "$ Income": "#F2DCDB",
                "$ Home Value": "#F2DCDB",
                "Owner Occupied": "#F2DCDB",
                "%Renter Occupied": "#F2DCDB",
                "Median Year Structure Built": "#F2DCDB",
                "House Count": "#DAEEF3",
                "House Penetration%": "#DAEEF3",
                "$ Total Spend": "#DAEEF3",
                "Total Visits": "#DAEEF3",
                "$ Average Order": "#DAEEF3",
                "Customer Profile Match Score": "#92D050",
                "Composite Score": "#92D050",
                "Penetration Flag": "#92D050",
                "Status": "#92D050",
                "Times Mailed To": "#E4DFEC",
                "Overall Mailing Qty": "#E4DFEC",
                "Overall RO's": "#E4DFEC",
                "Overall Responded": "#E4DFEC",
                "Overall Revenue": "#E4DFEC",
                "Overall Expense": "#E4DFEC",
                "Most Recent Mailed To": "#E4DFEC",
                "Response Rate": "#E4DFEC",
                "Overall ROAS": "#E4DFEC",
                "Response Rate %": "#E4DFEC"
            }
        }
    },
    "Automotive": {
        "features": {
            "use_wps": True,
            "use_cpms": True,
            "use_vds": True,
            "profile_modes": ["Dynamic (from file)", "Fixed Standard"]
        },
        "currency_columns": ["$ Income", "$ Home Value", "$ Total Spend", "$ Average Order"],
        "percentage_columns": ['% Children', '5+ Vehicles', '% 4 Vehicles', '% 3 Vehicles', '% 2 Vehicles', '% 1 Vehicle', '% No Vehicle'],
        "numeric_columns": [
            "Distance",
            "Selected",
            "Available",
            "Potential",
            "SFDU",
            "PO Box Res",
            "Seasonal",
            "Customer Count",
            "Customer Penetration%",
            "House Count",
            "Residence Count",
            "Business Count",
            "House Penetration%",
            "Total Visits",
            "Owner Occupied",
            "Median Year Structure Built",
        ],
        "required_columns_base": [
            'Distance', '$ Income', 'Owner Occupied', '5+ Vehicles', '% 4 Vehicles', '% 3 Vehicles', 
            '% 2 Vehicles', '% 1 Vehicle', '% No Vehicle'
        ],
        "required_columns_by_preset": {
            "Manual": [],
            "Auto Acquisition (No History)": [],
            "Auto Acquisition (With History + No Suppression)": [
                'House Count', 'House Penetration%', '$ Total Spend',
                'Total Visits', '$ Average Order', 'Selected'
            ],
            "Auto Acquisition (With History + Suppression)": [
                'House Count', 'House Penetration%', '$ Total Spend',
                'Total Visits', '$ Average Order', 'Selected'
            ]
        },
        "fail_filters": [
            { 
                "key" : 'min_income', 
                "label" : 'Min Household Income ($)', 
                "required_column" : '$ Income', 
                "threshold" : 40000, 
                "enabled": True
             },
            {
                "key" : 'max_income', 
                "label" : 'Max Household Income ($)', 
                "required_column" : '$ Income', 
                "threshold" : 250000, 
                "enabled": True  
            },
            {
                "key" : 'max_distance', 
                "label" : 'Max Distance (miles)', 
                "required_column" : 'Distance', 
                "threshold" : 50, 
                "enabled": True   
            },
            {
                "key" : 'min_owner', 
                "label" : 'Min Owner Occupied (%)', 
                "required_column" : 'Owner Occupied', 
                "threshold" : 70, 
                "enabled": False   
            },
            {
                "key" : 'max_penetration', 
                "label" : 'Max Penetration (%)', 
                "required_column" : 'House Penetration%', 
                "threshold" : 11.0, 
                "enabled": True   
            }
        ],
        "presets": {
            "Manual": {},
            "Auto Acquisition (No History)": {
                'Distance': 0.35,
                '$ Income': 0.25,
                'Vehicle Density Score': 0.40,
                'Weighted Penetration Score': 0.00,
                'Customer Profile Match Score': 0.00
            },
            "Auto Acquisition (With History + No Suppression)": {
                'House Count': 0.23,
                'Distance': 0.15,
                '$ Total Spend': 0.17,
                '$ Average Order': 0.11,
                '$ Income': 0.07,
                'House Penetration%': 0.06,
                'Total Visits': 0.06,
                'Vehicle Density Score': 0.15,
                'Customer Profile Match Score': 0.00, 
            },
             "Auto Acquisition (With History + Suppression)": {
                'House Count': 0.10,
                'Distance': 0.18,
                '$ Total Spend': 0.07,
                '$ Average Order': 0.05,
                '$ Income': 0.06,
                'House Penetration%': 0.03,
                'Total Visits': 0.04,
                'Vehicle Density Score': 0.12, 
                'Customer Profile Match Score': 0.20,
                'Weighted Penetration Score': 0.15
            },
        },
        "fallback_weights": {
            'Distance': 0.35,
            '$ Income': 0.25,
            'Vehicle Density Score': 0.40,
        },  
        "ideals_columns": {
            "$ Income": "Ideal Income",
            "$ Home Value": "Ideal Home Value",
            "Owner Occupied": "Ideal Owner Occupied",
            "Distance": "Ideal Distance",
            "Vehicle Density Score": "Ideal Vehicle Density Score",
            "% Children": "Ideal % Children",
        },
        "drivers": [
            "House Count",
            "House Penetration%",
            "$ Total Spend",
            "Total Visits",
            "$ Average Order"
        ],
        "profile_defaults": {
            "ideal_income": 65000,
            "ideal_home_value": 180000,
            "ideal_owner_occupied": 75,
            "ideal_distance": 25,
            "ideal_children": 0.20,
            "ideal_vehicle_density_score": 2.5
        },
        "export_layout": {
            "ranked_columns_order": [
                "Zip Code", "Geocode", "State", "City", "Distance", "Selected", "Available",
                "Potential", "Postal Rates", "$ Add’l Postage", "SFDU", "MFDU", "Trailers",
                "Customer Count", "Customer Penetration%", "House Count", "House Penetration%",
                "$ Total Spend", "Total Visits", "$ Average Order", "$ Income", "$ Home Value", 
                "Owner Occupied", "% Children", "% 1 Vehicle", "% 2 Vehicles", "% 3 Vehicles", 
                "% 4 Vehicles", "5+ Vehicles", "% No Vehicle", "Customer Profile Match Score", 
                "Composite Score", "Penetration Flag", "Status"
            ],
            "ranked_columns_drop": [ 
                "Segment Name", "Distance_Norm", "$ Income_Norm", "Vehicle Density Score",
                "Vehicle Density Score_Norm", "Business Count", "% Married, Spouse Present","Median Year Structure Built"
            ],
            "ranked_header_colors": {
                "Zip Code": "#FFFF54",
                "Geocode": "#FFFF54",
                "State": "#FFFF54",
                "City": "#FFFF54",
                "Distance": "#FFFF54",
                "Selected": "#FFFF54",
                "Available": "#FFFF54",
                "Potential": "#FFFF54",
                "Postal Rates": "#FFFF54",
                "$ Add’l Postage": "#FFFF54",
                "SFDU": "#FFFF54",
                "MFDU": "#DAEEF3",
                "Trailers": "#DAEEF3",
                "Customer Count": "#DAEEF3",
                "Customer Penetration%": "#DAEEF3",
                "House Count": "#DAEEF3",
                "House Penetration%": "#DAEEF3",
                "$ Total Spend": "#DAEEF3",
                "Total Visits": "#DAEEF3",
                "$ Average Order": "#DAEEF3",
                "$ Income": "#F2DCDB",
                "$ Home Value": "#F2DCDB",
                "Owner Occupied": "#F2DCDB",
                "% Children": "#F2DCDB",
                "% 1 Vehicle": "#F2DCDB",
                "% 2 Vehicles": "#F2DCDB",
                "% 3 Vehicles": "#F2DCDB",
                "% 4 Vehicles": "#F2DCDB",
                "5+ Vehicles": "#F2DCDB",
                "% No Vehicle": "#F2DCDB",
                "Customer Profile Match Score": "#92D050",
                "Composite Score": "#92D050",
                "Penetration Flag": "#92D050",
                "Status": "#92D050"
            },
            "include_winsor_sheet": True,
            "roi_columns_order": [
                "Zip Code", "Geocode", "State", "City", "Distance", "Selected", "Available",
                "Potential", "Postal Rates", "$ Add’l Postage", "SFDU", "MFDU", "Trailers",
                "Customer Count", "Customer Penetration%", "House Count", "House Penetration%",
                "$ Total Spend", "Total Visits", "$ Average Order", "$ Income", "$ Home Value", 
                "Owner Occupied", "% Children", "% 1 Vehicle", "% 2 Vehicles", "% 3 Vehicles", 
                "% 4 Vehicles", "5+ Vehicles", "% No Vehicle", "Customer Profile Match Score", 
                "Composite Score", "Penetration Flag", "Status","Times Mailed To", 
                "Overall Mailing Qty", "Overall RO's", "Overall Responded", "Overall Revenue", 
                "Overall Expense", "Most Recent Mailed To", "Response Rate", "Overall ROAS", 
                "Response Rate %"
            ],
            "roi_columns_drop": [
                "Segment Name", "Distance_Norm", "$ Income_Norm", "Vehicle Density Score",
                "Vehicle Density Score_Norm", "Business Count", "% Married, Spouse Present","Median Year Structure Built"
                ],
            "roi_header_colors": {
                "Zip Code": "#FFFF54",
                "Geocode": "#FFFF54",
                "State": "#FFFF54",
                "City": "#FFFF54",
                "Distance": "#FFFF54",
                "Selected": "#FFFF54",
                "Available": "#FFFF54",
                "Potential": "#FFFF54",
                "Postal Rates": "#FFFF54",
                "$ Add’l Postage": "#FFFF54",
                "SFDU": "#FFFF54",
                "MFDU": "#DAEEF3",
                "Trailers": "#DAEEF3",
                "Customer Count": "#DAEEF3",
                "Customer Penetration%": "#DAEEF3",
                "House Count": "#DAEEF3",
                "House Penetration%": "#DAEEF3",
                "$ Total Spend": "#DAEEF3",
                "Total Visits": "#DAEEF3",
                "$ Average Order": "#DAEEF3",
                "$ Income": "#F2DCDB",
                "$ Home Value": "#F2DCDB",
                "Owner Occupied": "#F2DCDB",
                "% Children": "#F2DCDB",
                "% 1 Vehicle": "#F2DCDB",
                "% 2 Vehicles": "#F2DCDB",
                "% 3 Vehicles": "#F2DCDB",
                "% 4 Vehicles": "#F2DCDB",
                "5+ Vehicles": "#F2DCDB",
                "% No Vehicle": "#F2DCDB",
                "Customer Profile Match Score": "#92D050",
                "Composite Score": "#92D050",
                "Penetration Flag": "#92D050",
                "Status": "#92D050",
                "Times Mailed To": "#E4DFEC",
                "Overall Mailing Qty": "#E4DFEC",
                "Overall RO's": "#E4DFEC",
                "Overall Responded": "#E4DFEC",
                "Overall Revenue": "#E4DFEC",
                "Overall Expense": "#E4DFEC",
                "Most Recent Mailed To": "#E4DFEC",
                "Response Rate": "#E4DFEC",
                "Overall ROAS": "#E4DFEC",
                "Response Rate %": "#E4DFEC"
            }
        }
    }
}
