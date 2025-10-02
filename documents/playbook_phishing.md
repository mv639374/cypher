# Phishing Incident Response Playbook

**Synopsis:** This playbook outlines the procedure for responding to confirmed phishing attempts. This applies to incidents involving suspicious emails, credential harvesting links, **malicious domains**, and **malicious URLs** reported by users or security tools.

## Section 1: Initial Analysis

Verify the sender, email headers, and link destinations to confirm the email is malicious.

## Section 2: Containment Procedure

**2.1 Block Sender Domain:** Add the sender's domain to the email gateway blocklist to prevent further emails from this source.

**2.2 Block Malicious URL:** If a malicious URL is present, add the URL to the web filter and network firewall blocklist.

## Section 3: User Communication

Notify the user who reported the email and send out a company-wide alert if the phishing campaign is widespread.