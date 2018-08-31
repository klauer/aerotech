import sys

header = '''<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>Form</class>
 <widget class="QWidget" name="Form">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>1194</width>
    <height>948</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>Form</string>
  </property>
  <layout class="QHBoxLayout" name="horizontalLayout">
   <item>
    <widget class="QScrollArea" name="scrollArea">
     <property name="widgetResizable">
      <bool>true</bool>
     </property>
     <widget class="QWidget" name="scrollAreaWidgetContents">
      <property name="geometry">
       <rect>
        <x>0</x>
        <y>0</y>
        <width>1000</width>
        <height>1000</height>
       </rect>
      </property>
     <layout class="QGridLayout" name="gridLayout">
'''

footer = '''
      </layout>
     </widget>
    </widget>
   </item>
  </layout>
 </widget>
 <customwidgets>
  <customwidget>
   <class>PyDMLabel</class>
   <extends>QLabel</extends>
   <header>pydm.widgets.label</header>
  </customwidget>
 </customwidgets>
 <resources/>
 <connections/>
</ui>
'''


parameter_template = '''
    <item row="{row}" column="{col_a}">
     <widget class="QLabel" name="Label{name}">
      <property name="font">
       <font>
        <weight>75</weight>
        <bold>true</bold>
       </font>
      </property>
      <property name="alignment">
       <set>Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter</set>
      </property>
      <property name="text">
       <string>{name}</string>
      </property>
     </widget>
    </item>
    <item row="{row}" column="{col_b}">
     <widget class="PyDMLabel" name="{name}">
      <property name="toolTip">
       <string>Parameter number {number} - {name}</string>
      </property>
      <property name="text">
       <string>...</string>
      </property>
      <property name="whatsThis"><string/>
      </property>
      <property name="displayFormat" stdset="0">
       <enum>PyDMLabel::{display_format}</enum>
      </property>
      <property name="channel" stdset="0">
       <string>ensemble://${{host}}:${{port}}@${{rate}}/GETPARM(${{axis}},{number})</string>
      </property>
     </widget>
    </item>
'''


if len(sys.argv) != 2:
    print('Usage: {} (parameter_list_filename.txt)'.format(sys.argv[0]))
    sys.exit(1)

parameter_fn = sys.argv[1]
parameters = open(parameter_fn).readlines()

row = 0
col_a = 0
col_b = 1

print(header)

if len(parameters) > 100:
    last_row = 50
else:
    last_row = 25


for parameter in parameters:
    parameter, number = parameter.strip().split(' ')
    if 'Setup' in parameter or 'Mask' in parameter:
        display_format = 'Hex'
    else:
        display_format = 'Default'
    print(parameter_template.format(row=row, number=number, name=parameter,
                                    col_a=col_a, col_b=col_b,
                                    display_format=display_format))
    row += 1
    if row == last_row:
        row = 0
        col_a += 2
        col_b += 2
print(footer)
