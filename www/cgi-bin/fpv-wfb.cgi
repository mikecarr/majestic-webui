#!/usr/bin/haserl
<%in p/common.cgi %>
<%in p/fpv_common.cgi %>
<%
set -x


# Set page title and determine active tab
page_title="WFB Settings"
label="$GET_tab"
[ -z "$label" ] && label="wireless"

# Debug function to log form submission data
debug_log() {
    echo "$1" >> /tmp/wfb_debug.log
}

# Function to determine if a channel is in the 2.4GHz range
is_24ghz_channel() {
    local channel="$1"
    # Channels 1-14 are in the 2.4GHz range
    if [ "$channel" -ge 1 ] && [ "$channel" -le 14 ]; then
        return 0  # True
    else
        return 1  # False
    fi
}

# Function to get the correct TX power based on channel frequency
get_tx_power_for_channel() {
    local channel="$1"
    
    # For YAML, always use the txpower field
    yaml_get_nested "$WFB_YAML" "wireless" "txpower"
    
}

# Function to set the correct TX power based on channel frequency
set_tx_power_for_channel() {
    local channel="$1"
    local power_value="$2"
    
    debug_log "Setting TX power: channel=$channel, power_value=$power_value"
    
    # For YAML, always use the txpower field
    yaml_set_value "$WFB_YAML" "wireless" "txpower" "$power_value"
    debug_log "Updated wireless.txpower: $power_value"

}

# Function to update all WFB values - handles both YAML and legacy formats
update_wfbinfo() {
    # Initialize variables with default values
    wfb_txpower="1"
    wfb_channel="161"
    wfb_width="20"
    wfb_frequency=""
    wfb_mcs_index="1"
    wfb_tun_index="1"
    wfb_fec_k="8"
    wfb_fec_n="12"
    wfb_stbc="0"
    wfb_ldpc="0"
    wfb_link_id="7669206"
    wfb_router="mavfwd"
    wfb_serial="ttyS2"
    wfb_osd_fps="20"
    
    
    # Using YAML configuration - get values from WFB_YAML
    debug_log "Reading from YAML configuration: $WFB_YAML"
    
    # Get Wireless Values
    yaml_txpower=$(yaml_get_value "$WFB_YAML" "wireless" "txpower")
    yaml_channel=$(yaml_get_value "$WFB_YAML" "wireless" "channel")
    yaml_width=$(yaml_get_value "$WFB_YAML" "wireless" "width")
    yaml_frequency=$(yaml_get_value "$WFB_YAML" "wireless" "frequency")
    
    # Get Broadcast Values
    yaml_mcs_index=$(yaml_get_value "$WFB_YAML" "broadcast" "mcs_index")
    yaml_tun_index=$(yaml_get_value "$WFB_YAML" "broadcast" "tun_index")
    yaml_fec_k=$(yaml_get_value "$WFB_YAML" "broadcast" "fec_k")
    yaml_fec_n=$(yaml_get_value "$WFB_YAML" "broadcast" "fec_n")
    yaml_stbc=$(yaml_get_value "$WFB_YAML" "broadcast" "stbc")
    yaml_ldpc=$(yaml_get_value "$WFB_YAML" "broadcast" "ldpc")
    yaml_link_id=$(yaml_get_value "$WFB_YAML" "broadcast" "link_id")
    
    # Get Telemetry Values
    yaml_router=$(yaml_get_value "$WFB_YAML" "telemetry" "router")
    yaml_serial=$(yaml_get_value "$WFB_YAML" "telemetry" "serial")
    yaml_osd_fps=$(yaml_get_value "$WFB_YAML" "telemetry" "osd_fps")
    
    # Update variables with values from YAML if they exist
    [ -n "$yaml_txpower" ] && wfb_txpower="$yaml_txpower"
    [ -n "$yaml_channel" ] && wfb_channel="$yaml_channel"
    [ -n "$yaml_width" ] && wfb_width="$yaml_width"
    [ -n "$yaml_frequency" ] && wfb_frequency="$yaml_frequency"
    [ -n "$yaml_mcs_index" ] && wfb_mcs_index="$yaml_mcs_index"
    [ -n "$yaml_tun_index" ] && wfb_tun_index="$yaml_tun_index"
    [ -n "$yaml_fec_k" ] && wfb_fec_k="$yaml_fec_k"
    [ -n "$yaml_fec_n" ] && wfb_fec_n="$yaml_fec_n"
    [ -n "$yaml_stbc" ] && wfb_stbc="$yaml_stbc"
    [ -n "$yaml_ldpc" ] && wfb_ldpc="$yaml_ldpc"
    [ -n "$yaml_link_id" ] && wfb_link_id="$yaml_link_id"
    [ -n "$yaml_router" ] && wfb_router="$yaml_router"
    [ -n "$yaml_serial" ] && wfb_serial="$yaml_serial"
    [ -n "$yaml_osd_fps" ] && wfb_osd_fps="$yaml_osd_fps"

    
    # Export for use in haserl
    export wfb_txpower wfb_channel wfb_width wfb_frequency
    export wfb_mcs_index wfb_tun_index wfb_fec_k wfb_fec_n wfb_stbc wfb_ldpc wfb_link_id
    export wfb_router wfb_serial wfb_osd_fps
    
    # Export section names for the tab labels
    export wfb_wireless="Wireless"
    export wfb_broadcast="Broadcast"
    export wfb_telemetry="Telemetry"
}

# Map numeric router value to string for UI display
map_router_value() {
    local numeric_value="$1"
    case "$numeric_value" in
        0) echo "mavfwd" ;;
        1) echo "mavrouter" ;;
        2) echo "msposd" ;;
        3) echo "ground" ;;
        *) echo "$numeric_value" ;; # Return as-is if not a recognized code
    esac
}


# Define available wireless channels
channels="1 2 3 4 5 6 7 8 9 10 11 12 13 14 36 40 44 48 52 56 60 64 100 104 108 112 116 120 124 128 132 136 140 149 153 157 161 165 169 173 177" 

# Define corresponding frequencies
frequencies="2412 2417 2422 2427 2432 2437 2442 2447 2452 2457 2462 2467 2472 2484 5180 5200 5220 5240 5260 5280 5300 5320 5500 5520 5540 5560 5580 5600 5620 5640 5660 5680 5700 5745 5765 5785 5805 5825 5845 5865 5885"

# Function to get the frequency for a given channel
get_frequency() {
    local channel="$1"
    local index=0
    for c in $channels; do
        if [ "$c" = "$channel" ]; then
            # Get the corresponding frequency
            frequency=$(echo "$frequencies" | awk "{print \$$((index+1))}")
            echo "$frequency"
            return
        fi
        index=$((index+1))
    done
    echo "Unknown" # Return "Unknown" if channel not found
}

# Function to create a label with tooltip
tooltip_label() {
    local name="$1"
    local label="$2"
    local tooltip="$3"
    
    echo "<label for=\"${name}\" class=\"form-label\">${label}"
    if [ -n "$tooltip" ]; then
        echo " <span class=\"badge bg-secondary rounded-circle\" style=\"cursor:help;font-size:10px;width:16px;height:16px;display:inline-flex;align-items:center;justify-content:center;\" data-bs-toggle=\"tooltip\" title=\"${tooltip}\">?</span>"
    fi
    echo "</label>"
}

# Function to generate channel options with channel-frequency pairs
field_channel_select() {
    local name="$1"
    local label="$2"
    local selected="$3"
    local tooltip="$4"
    
    echo "<p class=\"select\" id=\"${name}_wrap\">"
    tooltip_label "$name" "$label" "$tooltip"
    echo "<select class=\"form-select\" id=\"${name}\" name=\"${name}\">"
         
    for channel in $channels; do
        local frequency=$(get_frequency "$channel")
        local selected_attr=""
        if [ "$channel" = "$selected" ]; then
            selected_attr="selected"
        fi
        echo "<option value=\"${channel}\" ${selected_attr}>Channel ${channel} - ${frequency} MHz</option>"
    done
    
    echo "</select></p>"
}

# Function for select with tooltip
field_select_tooltip() {
    local name="$1"
    local label="$2"
    local selected="$3"
    local tooltip="$4"
    local min="$5"
    local max="$6"
    local step="$7"
    
    echo "<p class=\"select\" id=\"${name}_wrap\">"
    tooltip_label "$name" "$label" "$tooltip"
    echo "<select class=\"form-select\" id=\"${name}\" name=\"${name}\">"
    
    local current=$min
    while [ "$current" -le "$max" ]; do
        local selected_attr=""
        [ "$current" = "$selected" ] && selected_attr="selected"
        echo "<option value=\"$current\" $selected_attr>$current</option>"
        current=$((current + step))
    done
    
    echo "</select></p>"
}

# Custom function for boolean switches that uses numeric values (0/1)
field_numeric_switch_tooltip() {
    local name="$1"
    local label="$2"
    local value="$3"
    local tooltip="$4"
    
    local checked=""
    [ "$value" = "1" ] && checked="checked"
    
    echo "<p class=\"boolean\"><span class=\"form-check form-switch\">"
    echo "<input type=\"hidden\" id=\"${name}_off\" name=\"${name}\" value=\"0\">"
    echo "<input type=\"checkbox\" id=\"${name}\" name=\"${name}\" value=\"1\" class=\"form-check-input\" ${checked}>"
    tooltip_label "$name" "$label" "$tooltip"
    echo "</span></p>"
}

# Function for text input with tooltip
field_string_tooltip() {
    local name="$1"
    local label="$2"
    local value="$3"
    local tooltip="$4"
    local options="$5"
    
    echo "<p class=\"string\" id=\"${name}_wrap\">"
    tooltip_label "$name" "$label" "$tooltip"
    
    if [ -n "$options" ]; then
        echo "<select class=\"form-select\" id=\"${name}\" name=\"${name}\">"
        for option in $options; do
            local selected=""
            [ "$value" = "$option" ] && selected="selected"
            echo "<option value=\"${option}\" $selected>${option}</option>"
        done
        echo "</select>"
    else
        echo "<input type=\"text\" id=\"${name}\" name=\"${name}\" class=\"form-control\" value=\"${value}\">"
    fi
    echo "</p>"
}

# Handle form submission
if [ "$REQUEST_METHOD" = "POST" ]; then
    # Create a debug log entry for form submission
    debug_log "Form submitted with action: $POST_action"
    debug_log "Current tab: $label"
    
    case "$POST_action" in
        update)
            # Log all POST variables for debugging
            for var in $(set | grep ^POST_ | cut -d= -f1); do
                val=$(eval echo \$$var)
                debug_log "$var = $val"
            done
            
            # Process all form fields regardless of current tab

            # Update YAML configuration
            debug_log "Updating YAML configuration"
            
            # Wireless settings
            if [ -n "$POST_txpower" ]; then
                yaml_set_value "$WFB_YAML" "wireless" "txpower" "$POST_txpower"
                debug_log "Updated wireless.txpower: $POST_txpower"
            fi 

            if [ -n "$POST_channel" ]; then
                yaml_set_value "$WFB_YAML" "wireless" "channel" "$POST_channel"
                debug_log "Updated wireless.channel: $POST_channel"
            fi
            
            if [ -n "$POST_frequency" ]; then
                yaml_set_value "$WFB_YAML" "wireless" "frequency" "$POST_frequency"
                debug_log "Updated wireless.frequency: $POST_frequency"
            fi
            
            if [ -n "$POST_width" ]; then
                yaml_set_value "$WFB_YAML" "wireless" "width" "$POST_width"
                debug_log "Updated wireless.width: $POST_width"
            fi
            
            # Broadcast settings
            if [ -n "$POST_mcs_index" ]; then
                yaml_set_value "$WFB_YAML" "broadcast" "mcs_index" "$POST_mcs_index"
                debug_log "Updated broadcast.mcs_index: $POST_mcs_index"
            fi
            
            if [ -n "$POST_tun_index" ]; then
                yaml_set_value "$WFB_YAML" "broadcast" "tun_index" "$POST_tun_index"
                debug_log "Updated broadcast.tun_index: $POST_tun_index"
            fi
            
            if [ -n "$POST_fec_k" ]; then
                yaml_set_value "$WFB_YAML" "broadcast" "fec_k" "$POST_fec_k"
                debug_log "Updated broadcast.fec_k: $POST_fec_k"
            fi
            
            if [ -n "$POST_fec_n" ]; then
                yaml_set_value "$WFB_YAML" "broadcast" "fec_n" "$POST_fec_n"
                debug_log "Updated broadcast.fec_n: $POST_fec_n"
            fi
            
            # Handle the stbc switch - directly use numeric value (0 or 1)
            if [ -n "$POST_stbc" ]; then
                yaml_set_value "$WFB_YAML" "broadcast" "stbc" "$POST_stbc"
                debug_log "Updated broadcast.stbc: $POST_stbc"
            fi
            
            # Handle the ldpc switch - directly use numeric value (0 or 1)
            if [ -n "$POST_ldpc" ]; then
                yaml_set_value "$WFB_YAML" "broadcast" "ldpc" "$POST_ldpc"
                debug_log "Updated broadcast.ldpc: $POST_ldpc"
            fi
            
            if [ -n "$POST_link_id" ]; then
                yaml_set_value "$WFB_YAML" "broadcast" "link_id" "$POST_link_id"
                debug_log "Updated broadcast.link_id: $POST_link_id"
            fi
            
            # Telemetry settings
            if [ -n "$POST_router" ]; then
                yaml_set_value "$WFB_YAML" "telemetry" "router" "$POST_router"
                debug_log "Updated telemetry.router: $POST_router"
            fi
            
            if [ -n "$POST_serial" ]; then
                yaml_set_value "$WFB_YAML" "telemetry" "serial" "$POST_serial"
                debug_log "Updated telemetry.serial: $POST_serial"
            fi
            if [ -n "$POST_osd_fps" ]; then
                yaml_set_value "$WFB_YAML" "telemetry" "osd_fps" "$POST_osd_fps"
                debug_log "Updated telemetry.osd_fps: $POST_osd_fps"
            fi
                
            
            
            # Update local variables with new values
            update_wfbinfo
            # Redirect with success message
            redirect_back "success" "WFB settings updated."
            ;;
    esac
fi

# Call function to update local variables
update_wfbinfo

%>
<%in p/header.cgi %><!-- Initialize Bootstrap tooltips -->
<script>
document.addEventListener('DOMContentLoaded', function() {
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl)
  })
});

</script>

<!-- Navigation Tabs -->
<ul class="nav nav-underline small mb-4 d-lg-flex">
    
    <%
    # Manually set sections
    section="wireless broadcast telemetry"
    for key in $section; do
        locale=$(eval echo \$wfb_${key})
        if [ -z "$locale" ]; then
            # If no locale found, use capitalized key as fallback
            locale=$(echo "$key" | awk '{print toupper(substr($0,1,1)) substr($0,2)}')
        fi
        c="class=\"nav-link\""
        [ "$label" = "$key" ] && c="class=\"nav-link active\" aria-current=\"true\""
        echo "<li class=\"nav-item\"><a ${c} href=\"fpv-wfb.cgi?tab=${key}\">${locale}</a></li>"
    done
    %>
</ul>

<div class="row g-4">
    <div class="col col-md-6 col-lg-4 mb-4">
        
            <form action="<%= $SCRIPT_NAME %>" method="post">
            <% field_hidden "action" "update" %>
            <% field_hidden "current_tab" "$label" %>

        
        <%  if [ "$label" = "wireless" ]; then %>
            <div>
                <h3>Wireless</h3>

                <% field_channel_select "channel" "Wireless Channel" "$wfb_channel" "WiFi channel used for transmission. 2.4GHz (1-14) have better penetration, 5GHz (36-165) have less interference. Choose based on local conditions and regulations." %>
            
                <p class="range" id="txpower_wrap">
                    <% tooltip_label "txpower" "TX Power" "Transmit power in dBm. Higher values increase range but consume more power and may cause interference. Check local regulations for maximum allowed values." %>
                    <span class="input-group">
                        <input type="hidden" id="txpower" name="txpower" value="<%= $wfb_txpower %>">
                        <input type="range" class="form-control form-range" id="txpower-range" value="<%= $wfb_txpower %>" min="0" max="55" step="1">
                        <span class="input-group-text show-value" id="txpower-show"><%= $wfb_txpower %></span>
                    </span>
                </p>
                
                <p class="select" id="width_wrap">
                    <% tooltip_label "width" "Bandwidth" "Channel width in MHz. Wider channels (40/80) provide higher throughput but are more susceptible to interference. 20MHz is most reliable for long-range links." %>
                    <select class="form-select" id="width" name="width">
                        <option value="20" <% [ "$wfb_width" = "20" ] && echo "selected" %>>20 MHz</option>
                        <option value="40" <% [ "$wfb_width" = "40" ] && echo "selected" %>>40 MHz</option>
                    </select>
                </p>

            </div>
        <%  elif [ "$label" = "broadcast" ]; then %>
            <h3>Broadcast</h3>
            
            <% field_select_tooltip "mcs_index" "MCS Index" "$wfb_mcs_index" "MCS (Modulation and Coding Scheme) index determines bitrate and robustness. Lower values are more reliable in poor conditions but have lower throughput." 1 10 1 %>

            <% field_select_tooltip "tun_index" "TUN Index" "$wfb_tun_index" "Tunnel interface index for wifibroadcast. Multiple interfaces allow multiple video streams. Most setups use index 1 for the primary video." 1 10 1 %>

            <% field_select_tooltip "fec_k" "FEC K" "$wfb_fec_k" "Forward Error Correction K parameter - number of data packets per FEC block. Lower values provide better redundancy but lower efficiency." 1 15 1 %>
            
            <% field_select_tooltip "fec_n" "FEC N" "$wfb_fec_n" "Forward Error Correction N parameter - total number of packets per FEC block. The difference (N-K) determines redundant packets. Higher difference provides better error correction." 1 15 1 %>
            
            <% field_numeric_switch_tooltip "stbc" "STBC Enabled" "$wfb_stbc" "Space-Time Block Coding improves signal reliability in challenging environments by using multiple antennas. Enable for better range and resilience against interference." %>
            
            <% field_numeric_switch_tooltip "ldpc" "LDPC Enabled" "$wfb_ldpc" "Low-Density Parity-Check coding provides better error correction than standard coding. Enable for improved link quality at longer ranges." %>
            
            <% field_string_tooltip "link_id" "Link ID" "$wfb_link_id" "Unique identifier for this link. Must match between transmitter and receiver. Use different values for separate links to avoid interference." "" %>
            
        <%  elif [ "$label" = "telemetry" ]; then %>
            <h3>Telemetry</h3>

            <% field_string_tooltip "router" "Router" "$wfb_router" "Telemetry router type: mavfwd (basic forwarding), mavrouter (routing between interfaces), msposd (MultiWii Serial Protocol for OSD), or ground" "mavfwd mavrouter msposd ground" %>
            
            <%# <% field_string_tooltip "serial" "Serial Port" "$wfb_serial" "Serial port for telemetry data (e.g., ttyS0, ttyS1, ttyS2, ttyAMA0). Check your hardware documentation for the correct port." "" %> %>
            
            <p class="select" id="serial_port_wrap">
                <% tooltip_label "serial_port" "Serial Port" "Serial port for telemetry data (e.g., ttyS0, ttyS1, ttyS2, ttyAMA0). Check your hardware documentation for the correct port." %>
                <select class="form-select" id="serial_port" name="serial_port">
                    <option value="ttyS0" <% [ "$wfb_serial" = "ttyS0" ] && echo "selected" %>>ttyS0</option>
                    <option value="ttyS1" <% [ "$wfb_serial" = "ttyS1" ] && echo "selected" %>>ttyS1</option>
                    <option value="ttyS2" <% [ "$wfb_serial" = "ttyS2" ] && echo "selected" %>>ttyS2</option>
                    <option value="ttyAMA0" <% [ "$wfb_serial" = "ttyAMA0" ] && echo "selected" %>>ttyAMA0</option>
                    <option value="ttyAMA0" <% [ "$wfb_serial" = "ttyAMA1" ] && echo "selected" %>>ttyAMA1</option>
                </select>
            </p>

            <p class="select" id="osd_fps_wrap">
                <% tooltip_label "osd_fps" "OSD FPS" "On-Screen Display refresh rate. Higher values provide smoother OSD updates but use more bandwidth. 20-30 FPS is suitable for most applications." %>
                <select class="form-select" id="osd_fps" name="osd_fps">
                    <option value="10" <% [ "$wfb_osd_fps" = "10" ] && echo "selected" %>>10</option>
                    <option value="15" <% [ "$wfb_osd_fps" = "15" ] && echo "selected" %>>15</option>
                    <option value="20" <% [ "$wfb_osd_fps" = "20" ] && echo "selected" %>>20</option>
                    <option value="25" <% [ "$wfb_osd_fps" = "25" ] && echo "selected" %>>25</option>
                    <option value="30" <% [ "$wfb_osd_fps" = "30" ] && echo "selected" %>>30</option>
                </select>
            </p>
        <% fi %>
        
        <% button_submit %>
        
    </form>
    <br/>
    <div class="alert alert-danger">
        <h4>Restart Camera</h4>
        <p>Reboot camera to apply new settings and reset temporary files.</p>
        <a class="btn btn-danger" href="fw-restart.cgi">Restart Camera</a>
    </div>
</div>

<div class="col col-md-6 col-lg-8">
    <h4>Current Configuration</h4>
        <% ex "cat $WFB_YAML" %>

</div>

<!-- JavaScript for Range Sliders -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Function to update the text display when a range slider changes
    function setupRangeSlider(sliderId, displayId, hiddenId) {
        const slider = document.getElementById(sliderId);
        const display = document.getElementById(displayId);
        const hidden = document.getElementById(hiddenId);
        
        if (!slider || !display || !hidden) return;
        
        slider.addEventListener('input', function() {
            display.textContent = this.value;
            hidden.value = this.value;
        });
    }
    
    // Setup each range slider
    setupRangeSlider('txpower-range', 'txpower-show', 'txpower');
});
</script>

<%in p/footer.cgi %>