library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.add_tree_pkg.all;

entity add_tree_tb is
end add_tree_tb;

architecture rtl of add_tree_tb is
	constant clk_freq_c   : positive := 100000000;
	constant data_width_c : positive := 32; 
	constant num_inputs_c : positive := 13;
	constant pipelined_c  : boolean  := true;

	signal clk_s        : std_ulogic := '0';
	signal rst_s        : std_ulogic;
	signal en_s         : std_ulogic;
	signal input_s      : std_ulogic_vector (num_inputs_c*data_width_c - 1 downto 0);
	signal output_s     : std_ulogic_vector (data_width_c - 1 downto 0);

begin

	dut : add_tree generic map (
		num_inputs_g => num_inputs_c,
		data_width_g => data_width_c,
		pipelined_g  => pipelined_c
	) port map (
		clk_i    => clk_s,
		rst_i    => rst_s,
		en_i     => en_s,
		input_i  => input_s,
		output_o => output_s
	);

	clk_s <= not clk_s after ((1000000000/clk_freq_c)/2) * 1 ns;
		
	pipelined_test : if pipelined_c = true generate
		process 
		begin
			rst_s <= '0';

			wait until falling_edge(clk_s);
			report "Reset";
			rst_s <= '1';
			wait until falling_edge(clk_s);
			rst_s <= '0';

			en_s <= '1';
			
			input_s <=  X"F0C80AA7" & X"0F37F559" & 
						X"ADA5B58A" & X"525A4A75" & 
						X"665ED2A9" & X"99A12D57" & 
						X"AAAB0730" & X"5554F8CF" & 
						X"FD4BACBA" & X"02B45347" & 
						X"A54D1EA7" & X"5AB2E157" & X"5AB2E157";
			wait until falling_edge(clk_s);

			input_s <=  X"00000000" & X"00000000" & 
						X"00000000" & X"00000000" & 
						X"00000000" & X"00000000" & 
						X"00000000" & X"00000000" & 
						X"00000000" & X"00000000" & 
						X"00000000" & X"00000000" & X"00000000";
			wait until falling_edge(clk_s);
			
			input_s <=  X"00000001" & X"00000001" & 
						X"00000001" & X"00000001" & 
						X"00000001" & X"00000001" & 
						X"00000001" & X"00000001" & 
						X"00000001" & X"00000001" & 
						X"00000001" & X"00000001" & X"00000001";
			wait until falling_edge(clk_s);
			wait for 1 ns;

			input_s <=  X"F1C80AA7" & X"0F37F559" & 
						X"ADA5B58A" & X"525A4A75" & 
						X"665ED2A9" & X"99A12D57" & 
						X"AAAB0730" & X"5554F8CF" & 
						X"FD4BACBA" & X"02B45347" & 
						X"A54D1EA7" & X"5AB2E157" & X"5AB2E157";
			wait until falling_edge(clk_s);		
			wait for 1 ns;
			assert output_s = X"5AB2E154" severity error;

			input_s <=  X"F2C80AA7" & X"0F37F559" & 
						X"ADA5B58A" & X"525A4A75" & 
						X"665ED2A9" & X"99A12D57" & 
						X"AAAB0730" & X"5554F8CF" & 
						X"FD4BACBA" & X"02B45347" & 
						X"A54D1EA7" & X"5AB2E157" & X"5AB2E157";
			wait until falling_edge(clk_s);
			wait for 1 ns;
			assert output_s = X"00000000" severity error;
			
			input_s <=  X"F3C80AA7" & X"0F37F559" & 
						X"ADA5B58A" & X"525A4A75" & 
						X"665ED2A9" & X"99A12D57" & 
						X"AAAB0730" & X"5554F8CF" & 
						X"FD4BACBA" & X"02B45347" & 
						X"A54D1EA7" & X"5AB2E157" & X"5AB2E157";
			wait until falling_edge(clk_s);
			wait for 1 ns;
			assert output_s = X"0000000D" severity error;
			
			input_s <=  X"F4C80AA7" & X"0F37F559" & 
						X"ADA5B58A" & X"525A4A75" & 
						X"665ED2A9" & X"99A12D57" & 
						X"AAAB0730" & X"5554F8CF" & 
						X"FD4BACBA" & X"02B45347" & 
						X"A54D1EA7" & X"5AB2E157" & X"5AB2E157";
			wait until falling_edge(clk_s);
			wait for 1 ns;
			assert output_s = X"5BB2E154" severity error;
			wait until falling_edge(clk_s);
			wait for 1 ns;
			assert output_s = X"5CB2E154" severity error;
			wait until falling_edge(clk_s);
			wait for 1 ns;
			assert output_s = X"5DB2E154" severity error;
			wait until falling_edge(clk_s);
			wait for 1 ns;
			assert output_s = X"5EB2E154" severity error;
			wait until falling_edge(clk_s);

			-- input_s <= X"EFFFFFFF" & X"EFFFFFFF" & X"EFFFFFFF" & X"EFFFFFFF" & X"EFFFFFFF" & X"EFFFFFFF";
			-- wait until falling_edge(clk_s);

			-- input_s <= X"00000000" & X"00000000" & X"00000000" & X"00000000" & X"00000000" & X"00000000";
			-- wait until falling_edge(clk_s);
			
			-- input_s <= X"00000001" & X"00000001" & X"00000001" & X"00000001" & X"00000001" & X"00000001";
			-- wait until falling_edge(clk_s);
			-- wait for 1 ns;
			-- assert output_s = X"9FFFFFFA" severity error;

			-- input_s <= X"FFFFFFFF" & X"FFFFFFFF" & X"FFFFFFFF" & X"FFFFFFFF" & X"FFFFFFFF" & X"FFFFFFFF";
			-- wait until falling_edge(clk_s);		
			-- wait for 1 ns;
			-- assert output_s = X"00000000" severity error;

			-- input_s <= X"80000000" & X"80000000" & X"80000000" & X"80000000" & X"80000000" & X"80000000";
			-- wait until falling_edge(clk_s);
			-- wait for 1 ns;
			-- assert output_s = X"00000006" severity error;
			
			-- input_s <= X"80000001" & X"80000001" & X"80000001" & X"80000001" & X"80000001" & X"80000001";
			-- wait until falling_edge(clk_s);
			-- wait for 1 ns;
			-- assert output_s = X"FFFFFFFA" severity error;
			
			-- input_s <= X"80000000" & X"80000001" & X"80000002" & X"80000003" & X"80000004" & X"80000005";
			-- wait until falling_edge(clk_s);
			-- wait for 1 ns;
			-- assert output_s = X"00000000" severity error;
			-- wait until falling_edge(clk_s);
			-- wait for 1 ns;
			-- assert output_s = X"00000006" severity error;
			-- wait until falling_edge(clk_s);
			-- wait for 1 ns;
			-- assert output_s = X"0000000F" severity error;
			-- wait until falling_edge(clk_s);
				
			report "SIMULATION FINSIHED" severity failure;

		end process;


	end generate;


	not_pipelined_test : if pipelined_c = false generate
		process 
		begin
			input_s <= X"EFFFFFFF" & X"EFFFFFFF" & X"EFFFFFFF" & X"EFFFFFFF" & X"EFFFFFFF" & X"EFFFFFFF";
			wait until falling_edge(clk_s);
			wait for 1 ns;
			assert output_s = X"9FFFFFFA" severity error;

			input_s <= X"00000000" & X"00000000" & X"00000000" & X"00000000" & X"00000000" & X"00000000";
			wait until falling_edge(clk_s);
			wait for 1 ns;
			assert output_s = X"00000000" severity error;

			input_s <= X"00000001" & X"00000001" & X"00000001" & X"00000001" & X"00000001" & X"00000001";
			wait until falling_edge(clk_s);
			wait for 1 ns;
			assert output_s = X"00000006" severity error;

			input_s <= X"FFFFFFFF" & X"FFFFFFFF" & X"FFFFFFFF" & X"FFFFFFFF" & X"FFFFFFFF" & X"FFFFFFFF";
			wait until falling_edge(clk_s);
			wait for 1 ns;
			assert output_s = X"FFFFFFFA" severity error;

			input_s <= X"80000000" & X"80000000" & X"80000000" & X"80000000" & X"80000000" & X"80000000";
			wait until falling_edge(clk_s);
			wait for 1 ns;
			assert output_s = X"00000000" severity error;

			input_s <= X"80000001" & X"80000001" & X"80000001" & X"80000001" & X"80000001" & X"80000001";
			wait until falling_edge(clk_s);
			wait for 1 ns;
			assert output_s = X"00000006" severity error;

			input_s <= X"80000000" & X"80000001" & X"80000002" & X"80000003" & X"80000004" & X"80000005";
			wait until falling_edge(clk_s);
			wait for 1 ns;
			assert output_s = X"0000000F" severity error;
			
			report "SIMULATION FINSIHED" severity failure;
		end process;
	end generate;
		
	

end rtl;