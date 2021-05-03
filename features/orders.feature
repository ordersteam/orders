Feature: The orders service back-end
  As a Orders manager
  I need a RESTful order service
  So that I can keep track of all my orders

   Background:
    Given the following orders
      | customer_id | order_items                                 |
      | 1001         | 1234,2,35.1,SHIPPED&3456,1,1000.2,DELIVERED |
      | 1002         | 4567,3,5.60,CANCELLED                       |
      | 1003         | 7890,10,10,PLACED                           |
      | 1004         | 1000,10,10,DELIVERED                        |
      | 1005         | 1,1,1,SHIPPED                               |

 Scenario: The Server is running
    When I visit the "Home Page"
    Then I should see "Order RESTful Service" in the title
    And I should not see "404 Not Found"

  Scenario: Create an Order
    When I visit the "Home Page"
    And I set the "customer_id" to "1006"
    And I set the "item0_product_id" to "21"
    And I set the "item0_quantity" to "3"
    And I set the "item0_price" to "3.47"
    And I select "Placed" in the "item0_status" dropdown
    And I press the "add-row" button
    And I set the "item1_product_id" to "4"
    And I set the "item1_quantity" to "1"
    And I set the "item1_price" to "18.09"
    And I select "Shipped" in the "item1_status" dropdown
    And I press the "Create" button
    Then I should see the message "Success"
    When I copy the "id" field
    And I press the "Reset-Form" button
    Then the "id" field should be empty
    And the "customer_id" field should be empty
    And the "item0_product_id" field should be empty
    And the "item0_quantity" field should be empty
    And the "item0_price" field should be empty
    When I paste the "id" field
    And I press the "Retrieve" button
    Then I should see "1006" in the "customer_id" field
    And I should see "21" in the "item0_product_id" field
    And I should see "3" in the "item0_quantity" field
    And I should see "3.47" in the "item0_price" field
    And I should see "Placed" in the "item0_status" dropdown
    And I should see "4" in the "item1_product_id" field
    And I should see "1" in the "item1_quantity" field
    And I should see "18.09" in the "item1_price" field
    And I should see "Shipped" in the "item1_status" dropdown

  Scenario: List all orders
    When I visit the "Home Page"
    And I press the "List-All" button
    Then I should see the message "Success"
    And I should see order for customer_id "1001" in the results
    And I should see order for customer_id "1002" in the results
    And I should see order for customer_id "1003" in the results
     And I should not see order for customer_id "1009" in the results


  Scenario: List all orders for a customer id
    When I visit the "Home Page"
    And I set the "customer_id" to "1003"
    And I press the "find-by-customer-id" button
    Then I should see order for customer_id "1003" in the results
    And I should not see order for customer_id "1001" in the results
    And I should not see order for customer_id "1002" in the results
    And I should not see order for customer_id "1004" in the results


  Scenario: Update an Order
    When I visit the "Home Page"
    And I press the "List-All" button
    Then I should see the message "Success"
    And I should see order for customer_id "1001" in the results
    And I should see order for customer_id "1002" in the results
    And I should see order for customer_id "1003" in the results
    When I copy the "id" field
    And I set the "customer_id" to "999"
    And I press the "Update" button
    And I press the "Reset-Form" button
    Then the "id" field should be empty
    And the "customer_id" field should be empty
    When I paste the "id" field
    And I press the "Retrieve" button
    Then I should see "999" in the "customer_id" field  
  
  Scenario: Update an Order with incorrect Order ID
    When I visit the "Home Page"
    And I press the "List-All" button
    Then I should see the message "Success"
    And I should see order for customer_id "1001" in the results
    And I should see order for customer_id "1002" in the results
    And I should see order for customer_id "1003" in the results
    When I set the "id" to "0"
    And I set the "customer_id" to "666"
    And I press the "Update" button
    Then I should see the message "Order with id '0' was not found."

  Scenario: Read an order for an invalid id
    When I visit the "Home Page"
    And I set the "id" to "0"
    And I press the "Retrieve" button
    Then I should see the message "Order was not found."
    And the "customer_id" field should be empty

  Scenario: List all orders for an invalid cust id
    When I visit the "Home Page"
    And I set the "customer_id" to "12423"
    And I press the "find-by-customer-id" button
    Then I should not see order for customer_id "999" in the results
    And I should not see order for customer_id "1001" in the results
    And I should not see order for customer_id "1002" in the results
    And I should not see order for customer_id "1003" in the results  

  Scenario: Cancel an Order with shipped/delivered items
    When I visit the "Home Page"
    And I set the "customer_id" to "1001"
    And I press the "find-by-customer-id" button
    Then I should see the message "Success"
    And I should see "SHIPPED" in the results
    And I should see "DELIVERED" in the results
    When I copy the "id" field
    And I press the "Reset-Form" button
    Then the "id" field should be empty
    When I paste the "id" field
    And I press the "Retrieve" button
    And I press the "cancel" button
    Then I should see the message "All items have been shipped/delivered. Cannot cancel the order"

  Scenario: Delete an Order
    When I visit the "Home Page"
    And I press the "List-All" button
    Then I should see the message "Success"
    And I should see order for customer_id "1001" in the results
    And I should see order for customer_id "1002" in the results
    And I should see order for customer_id "1003" in the results
    When I copy the "id" field
    And I press the "Delete" button
    And I press the "Reset-Form" button
    Then the "id" field should be empty
    And the "customer_id" field should be empty
    When I paste the "id" field
    And I press the "Retrieve" button
    Then I should see the message "Order was not found."

  Scenario: Delete an order by id missing id
    When I visit the "Home Page"
    And I press the "List-All" button
    Then I should see the message "Success"
    And I should see order for customer_id "1001" in the results
    And I should see order for customer_id "1002" in the results
    And I should see order for customer_id "1003" in the results
    And I should not see order for id "999" in the results
    When I press the "Reset-Form" button
    Then the "id" field should be empty
    And the "customer_id" field should be empty
    When I set the "id" to "999"
    And I press the "Delete" button
    And I press the "List-All" button
    Then I should see the message "Success"
    And I should see order for customer_id "1001" in the results
    And I should see order for customer_id "1002" in the results
    And I should see order for customer_id "1003" in the results
    And I should not see order for id "999" in the results
